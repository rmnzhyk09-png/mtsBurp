/* Universal Android SSL unpinning (Frida 16/17, свой эмулятор Pixel_6).
 * Покрывает: X509TrustManager, SSLContext, OkHttp3 CertificatePinner,
 * HostnameVerifier, WebViewClient.onReceivedSslError + FLUTTER (Dart/boringssl).
 * Только свой device / свой трафик для отладки.
 */
'use strict';

function hookTrustManager() {
    try {
        var TM = Java.use('javax.net.ssl.X509TrustManager');
        ['checkClientTrusted', 'checkServerTrusted'].forEach(function (m) {
            TM[m].overload('[Ljava.security.cert.X509Certificate;', 'java.lang.String').implementation = function () { return; };
        });
        console.log('[+] TrustManager hooked');
    } catch (e) { console.log('[-] TrustManager: ' + e); }
}

function hookSSLContext() {
    try {
        var SC = Java.use('javax.net.ssl.SSLContext');
        SC.init.overload('[Ljavax.net.ssl.KeyManager;', '[Ljavax.net.ssl.TrustManager;', 'java.security.SecureRandom').implementation = function (km, tm, sr) {
            var TrustAll = Java.registerClass({
                name: 'com.mtsburp.TrustAll',
                implements: [Java.use('javax.net.ssl.X509TrustManager')],
                methods: {
                    checkClientTrusted: function () {},
                    checkServerTrusted: function () {},
                    getAcceptedIssuers: function () { return []; }
                }
            });
            return this.init(km, [TrustAll.$new()], sr);
        };
        console.log('[+] SSLContext hooked');
    } catch (e) { console.log('[-] SSLContext: ' + e); }
}

function hookOkHttp() {
    try {
        var CP = Java.use('okhttp3.CertificatePinner');
        CP.check.overload('java.lang.String', 'java.util.List').implementation = function () { return; };
        CP.check.overload('java.lang.String', '[Ljava.security.cert.Certificate;').implementation = function () { return; };
        console.log('[+] OkHttp3 CertificatePinner hooked');
    } catch (e) { console.log('[-] OkHttp3 (нет в приложении или уже обойден): ' + e); }
    try {
        var CP4 = Java.use('okhttp3.internal.tls.CertificateChainCleaner');
    } catch (e) { /* нет такого класса — нормально */ }
}

function hookHostnameVerifier() {
    try {
        var HV = Java.use('javax.net.ssl.HostnameVerifier');
        // Отдельные реализации (OkHostnameVerifier и др.) проще давить через класс:
        var OkHV = Java.use('okhttp3.internal.tls.OkHostnameVerifier');
        OkHV.verify.overload('java.lang.String', 'javax.net.ssl.SSLSession').implementation = function () { return true; };
        OkHV.verify.overload('java.lang.String', 'java.security.cert.X509Certificate').implementation = function () { return true; };
        console.log('[+] OkHostnameVerifier hooked');
    } catch (e) { console.log('[-] HostnameVerifier: ' + e); }
}

function hookWebView() {
    try {
        var WVC = Java.use('android.webkit.WebViewClient');
        WVC.onReceivedSslError.overload('android.webkit.WebView', 'android.webkit.SslErrorHandler', 'android.net.http.SslError').implementation = function (v, h, e) { h.proceed(); };
        console.log('[+] WebViewClient hooked');
    } catch (e) { console.log('[-] WebViewClient: ' + e); }
}

Java.perform(function () {
    console.log('[*] frida_unpin loaded, hooking...');
    hookTrustManager();
    hookSSLContext();
    hookOkHttp();
    hookHostnameVerifier();
    hookWebView();
    hookFlutter(); // сразу, если движок уже загружен
    // движок Flutter подгружается лениво (при открытии Flutter-экрана) —
    // проверяем каждые 2 сек, пока не зацепим:
    var flutterTimer = setInterval(function () {
        if (hookFlutter()) { clearInterval(flutterTimer); }
    }, 2000);
    console.log('[*] done. Трафик должен пойти через Burp 10.0.2.2:8080');
});

var flutterHooked = false;
function hookFlutter() {
    // Flutter/Dart использует свой boringssl внутри libflutter.so:
    // системный CA и Java-хуки он игнорирует. Давим верификацию цепочки.
    // Возвращает true если зацепили (или движок еще не загружен=false).
    if (flutterHooked) return true;
    try {
        var mod = Process.findModuleByName('libflutter.so');
        if (mod === null) { return false; }
        console.log('[*] Flutter: libflutter.so @ ' + mod.base);
        var names = [
            'ssl_crypto_x509_session_verify_cert_chain',
            'SSL_verify_cert_chain',
            'ssl_verify_cert_chain'
        ];
        var hooked = 0;
        names.forEach(function (n) {
            var addr = null;
            try { addr = mod.getExportByName(n); } catch (e) { /* нет экспорта */ }
            if (addr !== null) {
                Interceptor.attach(addr, {
                    onLeave: function (retval) {
                        // 1 / true = цепочка валидна
                        retval.replace(1);
                    }
                });
                console.log('[+] Flutter hooked: ' + n);
                hooked++;
            } else {
                console.log('[-] Flutter: нет символа ' + n);
            }
        });
        if (hooked === 0) { console.log('[-] Flutter: ни один символ не найден, нужен reflutter-патч APK'); return true; }
        flutterHooked = true;
        return true;
    } catch (e) { console.log('[-] Flutter: ' + e); return true; }
}
