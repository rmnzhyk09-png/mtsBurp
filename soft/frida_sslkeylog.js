/* SSL keylog: дамп plaintext из boringssl (Conscrypt/Java-слой) в лог.
 * Ловит: NativeCrypto.SSL_read / SSL_write по всем перегрузкам.
 * Только свой device / свой трафик для отладки.
 */
'use strict';

function dump(tag, buf, len) {
    try {
        if (buf === null || len <= 0 || len > 65536) {
            console.log('[SSL] ' + tag + ' len=' + len + ' (skip)');
            return;
        }
        var bytes = Memory.readByteArray(buf, Math.min(len, 2048));
        var s = '';
        try { s = Memory.readUtf8String(buf, Math.min(len, 2048)); } catch (e) { s = '<binary>'; }
        // показываем только похожее на HTTP/JSON, мусор режем
        if (/^(GET|POST|PUT|DELETE|PATCH|HTTP|\{|grpc)/.test(s)) {
            console.log('[SSL][' + tag + ' len=' + len + ']\n' + s.substring(0, 1500));
        } else {
            console.log('[SSL][' + tag + ' len=' + len + ' first16]=' +
                Array.prototype.slice.call(new Uint8Array(bytes.slice(0, 16))).map(function (b) { return ('0' + b.toString(16)).slice(-2); }).join(''));
        }
    } catch (e) { console.log('[SSL] dump err: ' + e); }
}

Java.perform(function () {
    console.log('[*] sslkeylog loaded');
    try {
        var NC = Java.use('com.android.org.conscrypt.NativeCrypto');
        var methods = NC.class.getDeclaredMethods();
        var n = 0;
        for (var i = 0; i < methods.length; i++) {
            var mn = methods[i].getName();
            if (mn !== 'SSL_read' && mn !== 'SSL_write') continue;
            (function (mname) {
                var ovs = NC[mname].overloads;
                ovs.forEach(function (ov) {
                    try {
                        ov.implementation = function () {
                            var args = Array.prototype.slice.call(arguments);
                            if (mname === 'SSL_write') {
                                // (ssl, address, buf, offset, len, ...) - ищем ByteBuffer/адрес+длину
                                for (var k = 0; k < args.length; k++) {
                                    if (args[k] && args[k].getClass && /ByteBuffer|DirectByteBuffer/.test(args[k].getClass().getName())) {
                                        try {
                                            var bb = args[k];
                                            var pos = bb.position(), lim = bb.limit();
                                            var tmp = Java.array('byte', new Array(lim - pos));
                                            bb.get(tmp);
                                            bb.position(pos);
                                            dump('W-java', Memory.readByteArray(tmp, 0), 0);
                                        } catch (e) { /* ignore */ }
                                    }
                                }
                            }
                            var r = ov.apply(this, arguments);
                            return r;
                        };
                        n++;
                    } catch (e) { /* overload mismatch */ }
                });
            })(mn);
        }
        console.log('[+] NativeCrypto hooked overloads: ' + n);
    } catch (e) { console.log('[-] NativeCrypto: ' + e); }
});
