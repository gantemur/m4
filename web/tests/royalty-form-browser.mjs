// Optional real-browser regression: CHROMIUM=/path/to/chromium node web/tests/royalty-form-browser.mjs
import assert from "node:assert/strict";
import {spawn} from "node:child_process";
import {createServer} from "node:http";
import {mkdtemp,readFile,rm} from "node:fs/promises";
import {tmpdir} from "node:os";
import {dirname,extname,join,resolve,sep} from "node:path";
import {fileURLToPath} from "node:url";

async function checkForm(frame) {
  const waitFor=async predicate=>{for(let i=0;i<200;i++){if(predicate())return;await new Promise(r=>setTimeout(r,20))}throw Error("Application initialization timed out")};
  await waitFor(()=>frame.contentDocument?.getElementById("royaltyForm")?.onsubmit);
  const win=frame.contentWindow,doc=win.document,get=id=>doc.getElementById(id),form=get("royaltyForm");
  doc.querySelector('[data-lang="en"]').click();
  await waitFor(()=>doc.documentElement.lang==="en");
  const field=name=>form.elements.namedItem(name),change=e=>e.dispatchEvent(new win.Event("change",{bubbles:true}));
  const select=get("officialPrice"),override=get("overridePrice"),results=[];
  const check=(condition,message)=>{if(!condition)throw Error(message)};
  const official=()=>{override.checked=false;select.value=select.options[1].value;change(select);field("quantity").disabled=false;field("fx").disabled=false;field("quantity").value="1000";field("fx").value="3500"};
  const submit=()=>form.dispatchEvent(new win.Event("submit",{bubbles:true,cancelable:true}));
  const amount=i=>Number(get("royaltyResult").querySelectorAll("dd")[i]?.textContent.match(/^[\d,.\s]+/)?.[0].replace(/[,\s]/g,""));
  const test=(name,fn)=>{try{fn();results.push({name,pass:true})}catch(error){results.push({name,pass:false,error:error.message})}};
  test("protected official price participates in native FormData",()=>{
    official();check(new win.FormData(form).get("price")==="77.33","Selected official price was omitted from FormData");
    check(field("price").readOnly,"Official price must be protected against edits");
  });
  test("real form submission uses the selected positive price",()=>{
    official();form.requestSubmit();check(amount(0)===270655000,`Expected assessed MNT 270655000; got ${amount(0)}`);
    check(amount(4)===21652400,`Expected hypothetical AMNAT MNT 21652400; got ${amount(4)}`);
  });
  test("empty selection clears official value, provenance and old result",()=>{
    official();submit();select.value="";change(select);
    check(field("price").value==="","Empty selection retained an official price");
    check(!field("price").readOnly&&!field("price").disabled,"Manual price must be editable");
    check(!get("officialPriceDetail").textContent&&!field("source").value,"Stale official provenance");
    check(!get("royaltyResult").textContent,"Stale calculated result");
  });
  test("manual price without an official row is honored",()=>{
    select.value="";change(select);field("price").value="100";submit();
    check(amount(0)===350000000,"Manual price was not submitted intact");
  });
  test("override survives synchronization and returning to official restores its price",()=>{
    official();override.checked=true;change(override);field("price").value="100";field("source").value="https://example.com/manual";submit();
    check(amount(0)===350000000,"Override price was reset or omitted");
    check(!get("officialPriceDetail").querySelector("a"),"Override still presented official provenance");
    override.checked=false;change(override);check(field("price").value==="77.33","Returning to official failed to restore its value");
    check(field("source").value.includes("mrpam.gov.mn"),"Official source was not restored");
  });
  for(const name of ["quantity","fx","price"]){
    for(const kind of ["blank","malformed","missing"]){
      test(`${kind} ${name} cannot become a determined zero`,()=>{
        official();select.value="";change(select);field("price").value="100";
        const e=field(name);e.disabled=false;e.value=kind==="malformed"?"not-a-number":kind==="blank"?"":e.value;
        if(kind==="missing")e.disabled=true;
        try{submit();check(!get("royaltyResult").querySelector("dd"),"Invalid/missing field produced a determined amount")}
        finally{e.disabled=false}
      });
    }
  }
  test("changing month or processing class leaves no stale official selection",()=>{
    official();field("month").value="2026-09";change(field("month"));
    check(select.value===""&&field("price").value==="","Month change retained the selected price");
    official();field("product_class").value="processed_coal";change(field("product_class"));
    check(select.value===""&&!field("source").value,"Class change retained official provenance");
  });
  test("selected record remains authoritative over a programmatic price change",()=>{
    official();field("price").value="1";submit();check(amount(0)===270655000,"Submitted price disagreed with selected record");
  });
  test("native required validation blocks an incomplete form",()=>{
    official();field("quantity").value="";get("royaltyResult").textContent="";form.requestSubmit();
    check(!form.checkValidity()&&!get("royaltyResult").textContent,"Incomplete form bypassed native validation");
  });
  test("explicit manual zero retains the existing zero-price semantics",()=>{
    official();select.value="";change(select);field("price").value="0";form.requestSubmit();
    check(amount(0)===0,"Explicit zero was confused with a missing price");
  });
  try{
    select.value="";change(select);field("product_class").value="processed_coal";change(field("product_class"));
    field("price").value="123.45";field("source").value="https://example.com/manual";
    doc.querySelector('[data-lang="mn"]').click();await waitFor(()=>doc.documentElement.lang==="mn");
    check(field("price").value==="123.45"&&field("product_class").value==="processed_coal","Language switch reset manual royalty inputs");
    check(field("source").value==="https://example.com/manual"&&!get("officialPriceDetail").querySelector("a"),"Language switch restored stale official provenance");
    field("quantity").value="";submit();check(get("royaltyResult").textContent.includes("хүчинтэй"),"Missing Mongolian input validation message");
    doc.querySelector('[data-lang="en"]').click();await waitFor(()=>doc.documentElement.lang==="en");submit();
    check(get("royaltyResult").textContent.includes("finite"),"Missing English input validation message");
    results.push({name:"manual royalty state and validation remain coherent in both languages",pass:true});
  }catch(error){results.push({name:"manual royalty state and validation remain coherent in both languages",pass:false,error:error.message})}
  return results;
}

const root=resolve(dirname(fileURLToPath(import.meta.url)),"../..");
const html=`<!doctype html><meta charset="utf-8"><iframe id="app" src="/web/index.html"></iframe><pre id="results">waiting</pre><script type="module">
const output=document.getElementById('results');try{const results=await (${checkForm.toString()})(document.getElementById('app'));output.dataset.status=results.every(r=>r.pass)?'passed':'failed';output.textContent=JSON.stringify(results)}catch(error){output.dataset.status='failed';output.textContent=error.stack}
</script>`;
const server=createServer(async(req,res)=>{
  try{
    const path=new URL(req.url,"http://localhost").pathname;
    if(path==="/__royalty_test"){res.setHeader("Content-Type","text/html");res.end(html);return}
    const local=resolve(root,"."+decodeURIComponent(path));
    if(!local.startsWith(root+sep+"web"+sep)){res.writeHead(404);res.end();return}
    res.setHeader("Content-Type",({".html":"text/html",".js":"text/javascript",".mjs":"text/javascript",".json":"application/json",".css":"text/css"})[extname(local)]||"application/octet-stream");
    res.end(await readFile(local));
  }catch{res.writeHead(404);res.end()}
});
const profile=await mkdtemp(join(tmpdir(),"royalty-browser-"));
try{
  await new Promise(r=>server.listen(0,"127.0.0.1",r));
  const browser=spawn(process.env.CHROMIUM||"chromium",["--headless","--no-sandbox","--disable-gpu","--disable-background-networking","--disable-component-update","--no-first-run","--no-default-browser-check",`--user-data-dir=${profile}`,"--remote-debugging-pipe"],{stdio:["ignore","ignore","pipe","pipe","pipe"],env:{...process.env,XDG_CONFIG_HOME:profile,XDG_CACHE_HOME:profile}});
  let sequence=0,buffer="",errors="";const pending=new Map();browser.stderr.on("data",data=>errors+=data);
  browser.stdio[4].on("data",data=>{buffer+=data;let end;while((end=buffer.indexOf("\0"))>=0){const message=JSON.parse(buffer.slice(0,end));buffer=buffer.slice(end+1);if(message.id&&pending.has(message.id)){const {accept,reject}=pending.get(message.id);pending.delete(message.id);message.error?reject(Error(JSON.stringify(message.error))):accept(message.result)}}});
  const send=(method,params={},sessionId)=>new Promise((accept,reject)=>{const id=++sequence;pending.set(id,{accept,reject});browser.stdio[3].write(JSON.stringify({id,method,params,...(sessionId?{sessionId}:{})})+"\0")});
  const timeout=setTimeout(()=>browser.kill("SIGKILL"),20000);
  browser.on("error",error=>{for(const p of pending.values())p.reject(error)});
  browser.on("close",()=>{for(const p of pending.values())p.reject(Error(errors||"Browser closed"))});
  try{
    const {targetId}=await send("Target.createTarget",{url:"about:blank"});
    const {sessionId}=await send("Target.attachToTarget",{targetId,flatten:true});
    await send("Page.navigate",{url:`http://127.0.0.1:${server.address().port}/__royalty_test`},sessionId);
    let result;
    for(let i=0;i<200;i++){
      const response=await send("Runtime.evaluate",{expression:"JSON.stringify({status:document.getElementById('results')?.dataset.status,text:document.getElementById('results')?.textContent})",returnByValue:true},sessionId);
      result=JSON.parse(response.result.value);if(result.status)break;await new Promise(r=>setTimeout(r,50));
    }
    console.log(result?.text||errors);assert.equal(result?.status,"passed","Royalty form browser regressions failed");
  }finally{clearTimeout(timeout);if(browser.exitCode===null&&browser.signalCode===null){const closed=new Promise(r=>browser.once("close",r));browser.kill();await closed}}
}finally{await new Promise(r=>server.close(r));await rm(profile,{recursive:true,force:true})}
