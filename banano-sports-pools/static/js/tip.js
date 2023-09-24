const tipAddress = "ban_113nqs3yd6ruh9ym45j6ngorgfyiof8qpxixypczcjxi15ukx1f66ffsn57k";

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
