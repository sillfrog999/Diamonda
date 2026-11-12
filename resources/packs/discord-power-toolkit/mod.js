(() => {
  const style=document.createElement('style');style.id='diamonda-discord-toolkit-style';
  style.textContent='html.diamonda-discord-compact [class*="messageListItem"],html.diamonda-discord-compact [class*="messageListItem"] [class*="contents"]{padding-top:1px!important;padding-bottom:1px!important}html.diamonda-discord-compact [class*="cozyMessage"]{min-height:0!important}#diamonda-discord-toolkit{position:fixed;z-index:2147483000;right:18px;bottom:20px;background:#20232b;color:#fff;border:1px solid #5865f2;border-radius:12px;padding:10px;font:12px Arial;box-shadow:0 8px 30px #0008}#diamonda-discord-toolkit button{display:block;width:100%;margin:5px 0;background:#5865f2;color:#fff;border:0;border-radius:7px;padding:8px;cursor:pointer}';
  document.documentElement.appendChild(style);
  const panel=document.createElement('div');panel.id='diamonda-discord-toolkit';panel.innerHTML='<b>DIAMONDA · DISCORD</b><button data-act="compact">Toggle Compact</button><button data-act="input">Focus Message Box</button><small>Ctrl + Shift + M / K</small>';document.documentElement.appendChild(panel);
  const compact=()=>document.documentElement.classList.toggle('diamonda-discord-compact');
  const focus=()=>{const el=document.querySelector('[role="textbox"][contenteditable="true"],div[contenteditable="true"][data-slate-editor="true"]');if(el)el.focus()};
  panel.addEventListener('click',e=>{const a=e.target.closest('button')?.dataset.act;if(a==='compact')compact();if(a==='input')focus()});
  const handler=e=>{if(!e.ctrlKey||!e.shiftKey)return;const k=e.key.toLowerCase();if(k==='m'){compact();e.preventDefault()}if(k==='k'){focus();e.preventDefault()}};document.addEventListener('keydown',handler,true);
  window.__diamondaCleanup=window.__diamondaCleanup||{};window.__diamondaCleanup[key]=()=>{document.removeEventListener('keydown',handler,true);document.documentElement.classList.remove('diamonda-discord-compact');panel.remove();style.remove()};
})();