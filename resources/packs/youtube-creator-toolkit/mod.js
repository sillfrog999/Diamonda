(() => {
  const panel = document.createElement('div');
  panel.id = 'diamonda-youtube-toolkit';
  panel.innerHTML = '<div class="dt-head">DIAMONDA · PLAYER</div><div class="dt-row"><button data-act="slower">− Speed</button><b data-speed>1.00×</b><button data-act="faster">+ Speed</button></div><div class="dt-row"><button data-act="pip">Picture-in-Picture</button><button data-act="theater">Theater</button></div><div class="dt-row"><button data-act="back">−5s</button><button data-act="forward">+5s</button></div>';
  const style = document.createElement('style');
  style.id = 'diamonda-youtube-toolkit-style';
  style.textContent = '#diamonda-youtube-toolkit{position:fixed;z-index:2147483000;right:18px;bottom:22px;background:#151923;color:#fff;border:1px solid #52627b;border-radius:12px;padding:10px;font:12px Arial;box-shadow:0 8px 30px #0008;min-width:220px}#diamonda-youtube-toolkit .dt-head{font-weight:800;letter-spacing:1px;margin:0 0 8px;color:#9fc4ff}#diamonda-youtube-toolkit .dt-row{display:flex;gap:6px;margin-top:6px;align-items:center;justify-content:space-between}#diamonda-youtube-toolkit button{background:#29364a;color:white;border:0;border-radius:7px;padding:7px 9px;cursor:pointer}#diamonda-youtube-toolkit button:hover{background:#416fa9}#diamonda-youtube-toolkit b{min-width:42px;text-align:center}';
  document.documentElement.appendChild(style); document.documentElement.appendChild(panel);
  const video = () => document.querySelector('video');
  const update = () => { const v=video(); panel.querySelector('[data-speed]').textContent=(v?v.playbackRate:1).toFixed(2)+'×'; };
  const clickTheater = () => { const b=document.querySelector('.ytp-size-button'); if(b) b.click(); };
  panel.addEventListener('click', async e => { const b=e.target.closest('button[data-act]'); if(!b)return; const v=video(); const a=b.dataset.act;
    if(a==='slower'&&v)v.playbackRate=Math.max(.25,v.playbackRate-.25);
    if(a==='faster'&&v)v.playbackRate=Math.min(4,v.playbackRate+.25);
    if(a==='back'&&v)v.currentTime=Math.max(0,v.currentTime-5);
    if(a==='forward'&&v)v.currentTime=Math.min(v.duration||Infinity,v.currentTime+5);
    if(a==='pip'&&v){try{if(document.pictureInPictureElement)await document.exitPictureInPicture();else await v.requestPictureInPicture();}catch(_){}}
    if(a==='theater')clickTheater(); update();
  });
  const onKey=e=>{if(!e.altKey||e.ctrlKey||e.metaKey)return;const v=video();if(!v)return;if(e.key==='ArrowLeft'){v.currentTime=Math.max(0,v.currentTime-5);e.preventDefault()}if(e.key==='ArrowRight'){v.currentTime=Math.min(v.duration||Infinity,v.currentTime+5);e.preventDefault()}};
  document.addEventListener('keydown',onKey,true);
  const timer=setInterval(update,1000); update();
  window.__diamondaCleanup=window.__diamondaCleanup||{};
  window.__diamondaCleanup[key]=()=>{clearInterval(timer);document.removeEventListener('keydown',onKey,true);panel.remove();style.remove()};
})();