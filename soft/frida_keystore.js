/* KeyStore spy: ловим пароль от .pfx и alias клиентского серта.
 * Только свой device / свой трафик для отладки.
 */
'use strict';

Java.perform(function () {
    console.log('[*] keystore-spy loaded');
    try {
        var KS = Java.use('java.security.KeyStore');
        KS.load.overload('java.io.InputStream', '[C').implementation = function (is, pass) {
            var pw = (pass === null) ? 'null' : Java.use('java.lang.String').$new(pass).toString();
            console.log('[KEYSTORE] load() password=[' + pw + ']');
            return this.load(is, pass);
        };
        KS.load.overload('java.security.KeyStore$LoadStoreParameter').implementation = function (p) {
            console.log('[KEYSTORE] load(param) class=' + (p ? p.getClass().getName() : 'null'));
            return this.load(p);
        };
        console.log('[+] KeyStore hooked');
    } catch (e) { console.log('[-] KeyStore: ' + e); }

    try {
        var KMF = Java.use('javax.net.ssl.KeyManagerFactory');
        KMF.init.overload('java.security.KeyStore', '[C').implementation = function (ks, pass) {
            var pw = (pass === null) ? 'null' : Java.use('java.lang.String').$new(pass).toString();
            console.log('[KEYSTORE] KeyManagerFactory.init() password=[' + pw + ']');
            return this.init(ks, pass);
        };
        console.log('[+] KeyManagerFactory hooked');
    } catch (e) { console.log('[-] KMF: ' + e); }

    try {
        var XKM = Java.use('javax.net.ssl.X509KeyManager');
        console.log('[+] X509KeyManager present');
    } catch (e) { console.log('[-] XKM: ' + e); }
});
