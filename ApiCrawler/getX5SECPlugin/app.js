let x5 = "";
function getCookie(){
  return new Promise((resolve) => {
    chrome.cookies.getAll({}, (cookies) => {
      resolve(
        cookies.filter(
          (cookie) => 
          cookie.domain.indexOf("tmall.com") !== -1 || 
          cookie.domain.indexOf("mmstat.com") !== -1 || 
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
      x5 += t.name + '=' + t.value + '; '
    }
    console.log(x5);
  });
}