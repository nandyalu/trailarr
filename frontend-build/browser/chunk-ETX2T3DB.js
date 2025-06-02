function s(t){let o=Math.floor(t/60),n=Math.floor(t%60);return o===0?`${n}m`:n===0?`${o}h`:`${o}h ${n}m`}var r=(t,o)=>t===o||JSON.stringify(t)===JSON.stringify(o);export{s as a,r as b};
