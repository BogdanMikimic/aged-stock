// in the table on the available stock page, each available stock is presented on a row
// this gets all the rows in the table
const offeredTrLst = document.querySelectorAll('.tr_offered')
const soldTrLst = document.querySelectorAll('.tr_sold')
const checkBoxUnderOffer = document.querySelector('#underOfferCB')
const checkBoxSold = document.querySelector('#soldCB')

const materialCsvStr = document.querySelector('#materialCsv')
const arrayOfMaterials = materialCsvStr.textContent.split(',')

const cbObjArray = []

const allTr = document.querySelectorAll('tr')


class HideStuff {
  constructor(name, allTrElements) {
    this.name = name;
    // these are all rows with available stock in the table
    this.alltr = allTrElements;
    this.getCheckbox = document.querySelector(('#' + this.name));
    this.getCheckbox.addEventListener('click', this.showMe.bind(this));
  }


  showMe() {
    if (this.getCheckbox.checked == 1) {
      for (const attr of this.alltr) {
        if (attr.getAttribute('data-material') == this.name) {
          attr.style.visibility = 'collapse'
        }
      }
    } else {
      for (const attr of this.alltr) {
        if (attr.getAttribute('data-material') == this.name) {
          if (attr.className == 'tr_offered') {
            if (checkBoxUnderOffer.checked != 1) {
              attr.style.visibility = 'visible'
              }
        } else if (attr.className == 'tr_sold') {
              if (checkBoxSold.checked != 1) {
              attr.style.visibility = 'visible'
            }
        } else {
            attr.style.visibility = 'visible'
        }

      }

    }
  }
}
}

// this creates a checkbox for each material (chocolate, nuts) in the active
for (const mat of arrayOfMaterials) {
  cbObjArray.push(new HideStuff(mat, allTr))
}

function showHideUnderOfer() {
  if (checkBoxUnderOffer.checked == 1) {
    for (const line of offeredTrLst) {
      line.style.visibility = 'collapse'
    }
  } else {
    // make it visible only if is not made invisible by individual material choices
    for (const line of offeredTrLst) {
      let material = line.getAttribute('data-material')
      for (const obj of cbObjArray) {
        if (obj.name == material) {
          if (obj.getCheckbox.checked != 1) {
            line.style.visibility = 'visible'
          }
        }
      }
    }
  }
}

checkBoxUnderOffer.addEventListener('click', showHideUnderOfer)

function showHideSold() {
  if (checkBoxSold.checked == 1) {
    for (const line of soldTrLst) {
      line.style.visibility = 'collapse'
    }
  } else {
    // make it visible only if is not made invisible by individual material choices
    for (const line of soldTrLst) {
      let material = line.getAttribute('data-material')
      for (const obj of cbObjArray) {
        if (obj.name == material) {
          if (obj.getCheckbox.checked != 1) {
            line.style.visibility = 'visible'
          }
        }
      }
    }
  }
}

checkBoxSold.addEventListener('click', showHideSold)
//showing/hiding the filter box
const filterContainer = document.querySelector("#div_filter_container")
filterContainer.style.display = "none"
const filterActivator = document.querySelector("#p_filter_message")


function showHideFiltContain(){
  if(filterContainer.style.display=="none")
  {
    filterContainer.style.display = "block"
    filterActivator.textContent = "(Click here to close filters ▲)"
  }
  else
  {
    filterContainer.style.display = "none"
    filterActivator.textContent = "(Click here to open filters ▼)"
  }
}

filterActivator.addEventListener('click', showHideFiltContain)

// Search bar
const searchBar = document.getElementById("searchBar")
const searchButton = document.querySelector("#searchButton")

searchButton.onmousedown = function(){
  searchButton.style.color = "red"
  searchButton.style.fontWeight = "bold"
  searchButton.style.backgroundColor = "#e5c07b"
}

searchButton.onmouseup = function(){
  searchButton.style.color = "#98c379"
  searchButton.style.fontWeight = "normal"
  searchButton.style.backgroundColor = "#282c34"
}

//does not search in filtered out (hidden) items
function searchSKU(){

  //reset previous search
  for (const itm of allTr){
    itm.style.display = 'table-row'
  }

  let text = searchBar.value.toLowerCase();
  // set current value of input searchbar to empty
  searchBar.value =""

  if (text ==''){
    for (const itm of allTr){
      itm.style.display = 'table-row'
    }

  }else{
  for (const itm of allTr){
    if(itm.style.visibility != "collapse"){
      if (itm.children[0].textContent.toLowerCase().includes(text)){

      }else{
        if (itm.children[0].textContent != "Product"){
          itm.style.display = 'none'
        }

      }
    }
}
}

}

searchButton.addEventListener("click", searchSKU)
