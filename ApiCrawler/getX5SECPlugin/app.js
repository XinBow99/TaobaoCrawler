let x5 = "";
function getCookie(){
  return new Promise((resolve) => {
    chrome.cookies.getAll({}, (cookies) => {
      resolve(
        cookies.filter((cookie) => cookie.name.indexOf("x5sec") !== -1)
      );
    });
  });
};
async function getX5(){
  await getCookie().then(result=>{x5 = result[0].value});
}