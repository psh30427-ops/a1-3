// Reproduce failure UX locally. No provider calls, real keys, or production changes.
import {chromium} from 'playwright';
import {spawn} from 'node:child_process';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import assert from 'node:assert/strict';
const root=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const origin='http://127.0.0.1:5313';
const server=spawn(process.env.PYTHON||'python',['scripts/serve.py','--port','5313'],{cwd:root,env:{...process.env,GEMINI_API_KEY:'',AI_ENABLED:'true',ALLOWED_ORIGIN:''},windowsHide:true,stdio:'pipe'});
let ready='';server.stdout.on('data',d=>ready+=d);let browser;
try {
 for(let i=0;i<60&&!ready.includes(origin);i++)await new Promise(r=>setTimeout(r,100));
 browser=await chromium.launch({channel:process.env.PLAYWRIGHT_CHANNEL||'chrome',headless:true});
 const page=await browser.newPage({viewport:{width:1200,height:950}});
 let scenario='empty';
 await page.route('**/api/recommend',async route=>{
  if(route.request().method()!=='POST')return route.continue();
  const timeout=scenario==='timeout';
  return route.fulfill({status:timeout?504:502,contentType:'application/json',body:JSON.stringify({error:{code:timeout?'timeout':'provider_error',message:timeout?'응답이 늦어지고 있습니다. 잠시 후 다시 시도해 주세요.':'Gemini 연결에 문제가 생겼습니다. 잠시 후 다시 시도해 주세요.'}})});
 });
 await page.goto(origin+'/#coach');
 await page.locator('#deck-stat').filter({hasText:'10'}).waitFor({state:'attached'});
 const submit=page.locator('#submit-coach');
 const out=path.join(root,'evidence/screenshots');
 const checks=[];
 for(const kind of ['empty','api-error','timeout']){
  scenario=kind;
  if(kind!=='empty'){await page.locator('#coach-question').fill('초보자에게 맞는 등록 덱을 추천해 주세요.');await page.locator('#ai-consent').check();}
  await submit.click();
  const expected=kind==='empty'?'궁금한 점이나 원하는 덱을 입력해 주세요.':kind==='timeout'?'응답이 늦어지고 있습니다. 잠시 후 다시 시도해 주세요.':'Gemini 연결에 문제가 생겼습니다. 잠시 후 다시 시도해 주세요.';
  await page.locator('#form-error').filter({hasText:expected}).waitFor();
  assert.equal(await submit.isDisabled(),false);
  await page.evaluate(()=>{document.querySelector('#page-coach').scrollIntoView();});
  await page.screenshot({path:path.join(out,`failure-${kind}.jpg`),type:'jpeg',quality:65,fullPage:true});
  checks.push({scenario:kind,message:expected,result:'passed',screenshot:`evidence/screenshots/failure-${kind}.jpg`});
 }
 await fs.writeFile(path.join(root,'evidence/failure-ux-results.json'),JSON.stringify({checkedAt:'2026-11-23',environment:'local browser; API errors and 504 mocked; not production incidents',providerCalls:0,checks},null,2)+'\n');
 console.log('PASS: empty input, mocked API 502, mocked timeout 504, retry button restored; zero provider calls.');
}finally{await browser?.close();server.kill();}
