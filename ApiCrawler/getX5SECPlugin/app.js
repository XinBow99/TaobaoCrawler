let x5 = "";
function getCookie(){
  return new Promise((resolve) => {
    chrome.cookies.getAll({}, (cookies) => {
      resolve(
        cookies.filter(
          (cookie) => 
          cookie.domain.indexOf("rate.tmall.com") !== -1 || 
          cookie.domain === ".tmall.com" || 
          cookie.domain.indexOf("alicdn.com") !== -1
        )
      );
    });
  });
};
async function getX5(){
  await getCookie().then(result=>{
    for(let rIndex = 0; rIndex < result.length; rIndex++){
      let t = result[rIndex];
      if(x5.indexOf(t.value) === -1){
      x5 += t.name + '=' + t.value + '; '
    }
    }
    console.log(x5);
  });
}