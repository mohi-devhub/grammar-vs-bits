"""Check every external PDF annotation and a requested repository redirect."""
import argparse,hashlib,re,subprocess,time,urllib.error,urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from qunti.common import ROOT,now,write_json


class Redirects(urllib.request.HTTPRedirectHandler):
    def __init__(self):self.hops=[]
    def redirect_request(self,request,fp,code,msg,headers,newurl):
        self.hops.append({'status':code,'from':request.full_url,'to':newurl})
        return super().redirect_request(request,fp,code,msg,headers,newurl)


def check(url):
    failures=[]
    for method in ('HEAD','GET','GET'):
        redirect=Redirects();opener=urllib.request.build_opener(redirect)
        try:
            request=urllib.request.Request(url,method=method,headers={'User-Agent':'Mozilla/5.0 (Grammar vs Bits link verification)','Range':'bytes=0-4095'})
            with opener.open(request,timeout=25) as response:
                if method=='GET':response.read(4096)
                return {'url':url,'ok':200<=response.status<300,'status':response.status,'final_url':response.url,'redirects':redirect.hops,'method':method,'earlier_failures':failures}
        except (urllib.error.URLError,TimeoutError) as exc:
            failures.append({'method':method,'status':getattr(exc,'code',None),'error_type':type(exc).__name__})
            time.sleep(1)
    return {'url':url,'ok':False,'failures':failures}


def main():
    p=argparse.ArgumentParser();p.add_argument('--pdf',type=Path,default=ROOT/'paper/main.pdf');p.add_argument('--old-url',required=True);p.add_argument('--expected-url',required=True);p.add_argument('--output',type=Path,default=ROOT/'results/ops/v0.1.1_pdf_links.json');args=p.parse_args()
    annotations=subprocess.check_output(['pdfinfo','-url',str(args.pdf)],text=True)
    urls=sorted(set(re.findall(r'https?://\S+',annotations)))
    if not urls:raise RuntimeError('No PDF links extracted')
    with ThreadPoolExecutor(max_workers=4) as pool:rows=list(pool.map(check,urls))
    old=check(args.old_url)
    redirect_ok=old['ok'] and old['final_url'].rstrip('/')==args.expected_url.rstrip('/') and bool(old['redirects'])
    result={'date':now(),'pdf':str(args.pdf.relative_to(ROOT)),'pdf_sha256':hashlib.sha256(args.pdf.read_bytes()).hexdigest(),
            'unique_pdf_links':len(urls),'all_pdf_links_resolve':all(r['ok'] for r in rows),'links':rows,
            'old_url_redirect':old,'old_url_redirects_to_canonical_repository':redirect_ok}
    write_json(args.output,result)
    print(f"PDF links: {sum(r['ok'] for r in rows)}/{len(rows)} resolve. Former URL redirects: {redirect_ok}.")
    if not result['all_pdf_links_resolve'] or not redirect_ok:raise RuntimeError('Link/redirect checks failed; inspect the saved report')

if __name__=='__main__':main()
