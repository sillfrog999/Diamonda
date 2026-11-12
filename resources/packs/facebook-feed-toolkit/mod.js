(() => {
  const style=document.createElement('style');style.id='diamonda-facebook-toolkit-style';
  style.textContent='html.diamonda-focus-feed [role="complementary"]{display:none!important}html.diamonda-focus-feed [aria-label*="Stories"],html.diamonda-focus-feed [aria-label*="story"],html.diamonda-focus-feed [aria-label*="Reels"]{display:none!important}#diamonda-facebook-toolkit{position:fixed;z-index:2147483000;right:18px;bottom:20px;background:#14263d;color:#fff;border:1px solid #5279a8;border-radius:12px;padding:10px;font:12px Arial;box-shadow:0 8px 30px #0008}#diamonda-facebook-toolkit button{display:block;width:100%;margin:5px 0;background:#24558b;color:#fff;border:0;border-radius:7px;padding:8px;cursor:pointer}';
  document.documentElement.appendChild(style);
  const panel=document.createElement('div');panel.id='diamonda-facebook-toolkit';panel.innerHTML='<b>DIAMONDA · FEED</b><button data-act="focus">Toggle Focus Feed</button><button data-act="top">Back to top</button><small>Alt + Shift + F</small>';document.documentElement.appendChild(panel);
  const toggle=()=>document.documentElement.classList.toggle('diamonda-focus-feed');
  panel.addEventListener('click',e=>{const a=e.target.closest('button')?.dataset.act;if(a==='focus')toggle();if(a==='top')window.scrollTo({top:0,behavior:'smooth'})});
  const handler=e=>{if(e.altKey&&e.shiftKey&&e.key.toLowerCase()==='f'){toggle();e.preventDefault()}};document.addEventListener('keydown',handler,true);
  window.__diamondaCleanup=window.__diamondaCleanup||{};window.__diamondaCleanup[key]=()=>{document.removeEventListener('keydown',handler,true);document.documentElement.classList.remove('diamonda-focus-feed');panel.remove();style.remove()};
})();