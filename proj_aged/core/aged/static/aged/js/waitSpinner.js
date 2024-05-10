const pdfDownloadFrmTag = document.querySelector('#pdfDownload')
const loaderDivTag = document.querySelector('#loader')
const getPdfButTag = document.querySelector('#getPdf')


function spin(){

  pdfDownloadFrmTag.style.display = "None"
  loaderDivTag.style.display = "block"
  setTimeout(function(){ loaderDivTag.style.display = "None"; }, 3000);


}

getPdfButTag.addEventListener('click', spin)
