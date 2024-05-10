const checkBoxUnderOffer = document.querySelector('#Offered')
const listTrUnderOffer = document.querySelectorAll('.Offered')
const checkBoxSold = document.querySelector('#Sold')
const listTrSold = document.querySelectorAll('.Sold')
const checkBoxDeclined = document.querySelector('#Declined')
const listTrDeclined = document.querySelectorAll('.Declined')
const checkBoxOfferExpired = document.querySelector('#OfferExpired')
const listTrOfferExpired = document.querySelectorAll('.OfferExpired')

function showHideUnderOfer() {
  if (checkBoxUnderOffer.checked == 1) {
    for (const line of listTrUnderOffer) {
      line.style.visibility = 'collapse'
    }
  } else {
    for (const line of listTrUnderOffer) {
            line.style.visibility = 'visible'
          }
        }
      }

checkBoxUnderOffer.addEventListener('click', showHideUnderOfer)

function showHideSold() {
  if (checkBoxSold.checked == 1) {
    for (const line of listTrSold) {
      line.style.visibility = 'collapse'
    }
  } else {
    for (const line of listTrSold) {
            line.style.visibility = 'visible'
          }
        }
      }

checkBoxSold.addEventListener('click', showHideSold)

function showHideDeclined() {
  if (checkBoxDeclined.checked == 1) {
    for (const line of listTrDeclined) {
      line.style.visibility = 'collapse'
    }
  } else {
    for (const line of listTrDeclined) {
            line.style.visibility = 'visible'
          }
        }
      }

checkBoxDeclined.addEventListener('click', showHideDeclined)

function showHideOfferExpired() {
  if (checkBoxOfferExpired.checked == 1) {
    for (const line of listTrOfferExpired) {
      line.style.visibility = 'collapse'
    }
  } else {
    for (const line of listTrOfferExpired) {
            line.style.visibility = 'visible'
          }
        }
      }

checkBoxOfferExpired.addEventListener('click', showHideOfferExpired)


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
