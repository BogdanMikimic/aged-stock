let today = new Date()
let dd = today.getDate()
let mm = today.getMonth() + 1 //January is 0!
let yyyy = today.getFullYear()

if (dd < 10) {
   dd = '0' + dd;
}

if (mm < 10) {
   mm = '0' + mm;
}



today = yyyy + '-' + mm + '-' + dd;

// set max date as today for start of interval

const start = document.getElementById("start")
start.setAttribute("max", today)
