// Local presentation only. The Python application owns checkout calculations.
document.querySelector('#quantity').addEventListener('input', event => {
  const quantity = Number(event.target.value);
  const total = Number.isInteger(quantity) && quantity >= 0 ? quantity * 12.5 : 0;
  document.querySelector('#total').textContent = `$${total.toFixed(2)}`;
});
