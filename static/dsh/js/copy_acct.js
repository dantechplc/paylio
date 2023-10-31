
    function copyAccountNumber() {
      const accountNumber = document.getElementById('accountNumber').innerText;
      const dummyInput = document.createElement('textarea');
      document.body.appendChild(dummyInput);
      dummyInput.value = accountNumber;
      dummyInput.select();
      document.execCommand('copy');
      document.body.removeChild(dummyInput);
      alert(accountNumber);
    }
