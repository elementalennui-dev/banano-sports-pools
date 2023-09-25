const tipAddress = "ban_3zwj9qo66y1tyz6uicoh8bmossuiuwyefig1yx3zwzmoeqji9wbqdu3egka9";

function makeTipQRCode() {
  $("#tip_qrcode").empty();
  let qrUrl = `banano:${tipAddress}`;
  let qrcode = new QRCode(document.getElementById('tip_qrcode'), {
      text: qrUrl,
      width: 128,
      height: 128,
      colorDark: '#000',
      colorLight: '#fff',
      correctLevel: QRCode.CorrectLevel.H
  });
  $("#tip_qrcode > img").css({"margin":"auto"});
}
