/* Enum: какие SSL-символы экспортирует каждый модуль (для перехвата plaintext). */
'use strict';

Java.perform(function () {
    var targets = ['SSL_write', 'SSL_read', 'SSL_get_servername',
        'ssl_crypto_x509_session_verify_cert_chain',
        'SSL_use_certificate', 'SSL_use_PrivateKey',
        'SSL_CTX_set_verify', 'SSL_set_verify'];
    Process.enumerateModules().forEach(function (m) {
        var name = m.name;
        if (name.indexOf('flutter') < 0 && name.indexOf('cronet') < 0 &&
            name.indexOf('ssl') < 0 && name.indexOf('crypto') < 0 &&
            name.indexOf('conscrypt') < 0 && name.indexOf('okhttp') < 0) return;
        try {
            var exps = m.enumerateExports();
            exps.forEach(function (e) {
                if (targets.indexOf(e.name) >= 0) {
                    console.log('[EXPORT] ' + name + ' :: ' + e.name + ' @ ' + e.address);
                }
            });
        } catch (err) { /* skip */ }
    });
    console.log('[*] enum done');
});
