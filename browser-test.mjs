import {chromium} from 'playwright';
import {spawn} from 'node:child_process';
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const catalog=JSON.parse((await fs.readFile(path.join(root,'public/data/catalog.json'),'utf8')).replace(/^\uFEFF/,''));
const origin='http://127.0.0.1:5311';
const server=spawn(process.env.PYTHON||'python',['scripts/serve.py','--port','5311'],{cwd:root,env:{...process.env,GEMINI_API_KEY:'',AI_ENABLED:'true',ALLOWED_ORIGIN:''},windowsHide:true,stdio:'pipe'});
let output='';server.stdout.on('data',s=>output+=s);server.stderr.on('data',s=>output+=s);
let browser;
try{
 for(let i=0;i<60;i++){if(server.exitCode!==null)throw Error(output);if(output.includes(origin))break;await new Promise(r=>setTimeout(r,100));}
 const response=await fetch(origin);assert.equal(response.status,200);
 browser=await chromium.launch({channel:process.env.PLAYWRIGHT_CHANNEL||'chrome',headless:true});
 const page=await browser.newPage({viewport:{width:1440,height:1000}});page.setDefaultTimeout(7000);
 const errors=[],external=[];page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(!r.url().startsWith(origin)&&!r.url().startsWith('data:'))external.push(r.url())});
 await page.goto(origin);await page.waitForFunction(()=>document.querySelector('#deck-stat').textContent==='10');await page.screenshot({path:path.join(root,'evidence/screenshots/desktop-home.png'),fullPage:true});
 await page.getByRole('navigation',{name:'주 메뉴'}).getByRole('link',{name:'덱 탐색'}).click();assert.equal(await page.locator('.deck-card').count(),10);
 await page.getByRole('searchbox',{name:'덱과 카드 이름 검색'}).fill('메가나무킹');assert.equal(await page.locator('.deck-card').count(),1);await page.locator('.deck-open').first().click();await page.locator('#dialog-content').getByText('공략 사이트 평가 · GameWith Tier 2',{exact:true}).waitFor();assert.ok((await page.locator('#dialog-content').innerText()).includes('2026-11-18'));await page.keyboard.press('Escape');
 await page.getByRole('searchbox',{name:'덱과 카드 이름 검색'}).fill('멜메탈');assert.equal(await page.locator('.deck-card').count(),1);
 await page.getByRole('button',{name:/멜메탈.*즐겨찾기/}).click();await page.reload();await page.locator('.deck-card').first().waitFor();assert.equal(await page.locator('.favorite-button[aria-pressed=true]').count(),1);
 await page.getByRole('button',{name:'♡ 즐겨찾기만'}).click();assert.equal(await page.locator('.deck-card').count(),1);
 await page.getByRole('button',{name:/멜메탈.*상세 보기/}).click();const dialog=page.getByRole('dialog');await dialog.waitFor();const d=catalog.decks[0];assert.equal(await dialog.locator('tbody tr').count(),d.cards.length);for(const c of d.cards)assert.equal(await dialog.locator(`tr[data-card-id="${c.id}"] td`).last().innerText(),`× ${c.quantity}`);assert.ok((await dialog.innerText()).includes('합계 20장'));await page.keyboard.press('Escape');
 await page.getByRole('button',{name:'초기화',exact:true}).click();await page.getByRole('combobox',{name:'속성 필터'}).selectOption('물');assert.equal(await page.locator('.deck-card').count(),1);await page.getByRole('searchbox').fill('없는 덱');await page.getByText('조건에 맞는 덱이 없어요').waitFor();await page.getByRole('button',{name:'초기화',exact:true}).click();
 await page.getByRole('navigation').getByRole('link',{name:'AI 상담'}).click();await page.getByRole('button',{name:/내게 맞는 덱 상담하기/}).click();assert.ok((await page.locator('#form-error').innerText()).includes('입력'));
 await page.getByLabel('궁금한 점',{exact:false}).fill('멜메탈을 좋아해요. 차분하게 준비하는 덱을 추천해 주세요.');await page.getByRole('button',{name:/내게 맞는 덱 상담하기/}).click();assert.ok((await page.locator('#form-error').innerText()).includes('외부 전송'));
 await page.locator('#ai-consent').check();await page.getByRole('button',{name:/내게 맞는 덱 상담하기/}).click();await page.getByRole('heading',{name:'상담을 완료하지 못했어요'}).waitFor();assert.ok((await page.locator('#form-error').innerText()).includes('연결을 준비'));
 await page.screenshot({path:path.join(root,'evidence/screenshots/ai-not-configured.png'),fullPage:true});
 await page.getByRole('button',{name:'결과 예시 보기 ↗'}).click();assert.ok((await page.locator('.result-badge').innerText()).includes('실제 AI 호출 아님'));
 const mock={mode:'test',summary:'검증용 모의 API 응답입니다. 실제 Gemini 호출 결과가 아닙니다.',recommendations:[{deckId:d.id,reason:'차분한 운영과 강철 속성 선호에 맞춰 등록 덱을 살펴볼 수 있습니다.',playSteps:d.strategy,cautions:d.weaknesses}],unknowns:['현재 티어·승률과 정확한 보유 수량은 미확인입니다.'],dataCheckedAt:'2026-10-30'};
 await page.route('**/api/recommend',async route=>{if(route.request().method()==='POST'){const input=route.request().postDataJSON();assert.equal(input.consent,true);await route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(mock)});}else await route.continue();});
 await page.locator('#coach-type').selectOption('강철');await page.locator('#owned-cards').fill('멜탄, 멜메탈 ex');await page.locator('#coach-style').selectOption('defensive');await page.getByRole('button',{name:/내게 맞는 덱 상담하기/}).click();await page.getByText('검증용 모의 응답 · 실제 AI 호출 아님',{exact:true}).waitFor();assert.equal(await page.locator('.recommendation').count(),1);assert.ok((await page.locator('.source-line').innerText()).includes('2026-10-30'));await page.screenshot({path:path.join(root,'evidence/screenshots/ai-mock-flow.png'),fullPage:true});
 mock.recommendations[0].reason='<img src=x onerror="window.badInjection=true">';await page.getByRole('button',{name:/내게 맞는 덱 상담하기/}).click();await page.getByText(mock.recommendations[0].reason,{exact:true}).waitFor();assert.equal(await page.locator('img[src=x]').count(),0);assert.equal(await page.evaluate(()=>Boolean(window.badInjection)),false);
 await page.unroute('**/api/recommend');await page.route('**/api/recommend',async route=>{if(route.request().method()==='POST')await route.fulfill({status:504,contentType:'application/json',body:JSON.stringify({error:{message:'응답이 늦어지고 있습니다. 잠시 후 다시 시도해 주세요.'}})});else await route.continue();});await page.getByRole('button',{name:/내게 맞는 덱 상담하기/}).click();await page.locator('#form-error').filter({hasText:'응답이 늦어지고'}).waitFor();assert.equal(await page.locator('#submit-coach').isDisabled(),false);
 await page.getByRole('navigation').getByRole('link',{name:'출처 안내'}).click();assert.equal(await page.locator('.source-item').count(),10);await page.locator('.source-item summary').first().click();assert.ok((await page.locator('.source-item').first().innerText()).includes('2026-10-30'));
 for(const width of [1440,768,390]){await page.setViewportSize({width,height:900});for(const route of ['home','decks','coach','sources']){await page.goto(origin+'/#'+route);await page.waitForFunction(()=>document.querySelector('#deck-stat').textContent==='10');assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`overflow at ${width}/${route}`);}}
 await page.setViewportSize({width:390,height:844});await page.goto(origin);await page.waitForFunction(()=>document.querySelector('#deck-stat').textContent==='10');await page.screenshot({path:path.join(root,'evidence/screenshots/mobile-home.png'),fullPage:true});await page.goto(origin+'/#decks');await page.locator('.deck-card').first().waitFor();await page.screenshot({path:path.join(root,'evidence/screenshots/mobile-decks.png'),fullPage:true});
 assert.deepEqual(errors,[]);assert.deepEqual(external,[]);
 const result={testedAt:'2026-11-19',result:'passed',screens:[1440,768,390],checks:['4-menu navigation','10 actual twenty-card recipes','search/type/favorite persistence','empty input/consent/real 503','mock API success with explicit test badge','upstream timeout message and retry','text-only output prevents HTML execution','source dates','no overflow','no external browser requests','no page errors'],liveAiVerified:false,deployedUrlVerified:false};await fs.writeFile(path.join(root,'evidence/browser-results.json'),JSON.stringify(result,null,2)+'\n');console.log('PASS: navigation, 20-card lists, search/filter/favorites, input errors, real missing-key 503, labelled mock success, timeout retry, XSS text rendering, sources, responsive screens, no external requests. Live AI and deployed URL: NOT verified.');
}finally{await browser?.close();server.kill();}


