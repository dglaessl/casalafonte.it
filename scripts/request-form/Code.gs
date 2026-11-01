/**
 * Casa La Fonte booking requests — Google Apps Script web app.
 * Receives the website's request form, saves it to this spreadsheet, emails the hosts,
 * and sends the guest a short confirmation in their language.
 *
 * Setup (once): create a Google Sheet, open Extensions > Apps Script, paste this file,
 * then Deploy > New deployment > Web app, "Execute as: Me", "Who has access: Anyone".
 * Copy the web app URL into index.html (CLF_REQ_URL) and rebuild the language pages.
 */
const HOSTS = 'dglaessl@gmail.com';   // add Eva with a comma to copy her on every request
const SHEET_NAME = 'Requests';
const LANGS = ['en', 'de', 'it', 'nl', 'da', 'fr'];

function doPost(e) {
  try {
    const d = JSON.parse((e && e.postData && e.postData.contents) || '{}');
    if (d.hp) return out_({ ok: true });                                // honeypot: a bot filled the hidden field
    const email = String(d.email || '').trim().slice(0, 120);
    const name = String(d.name || '').replace(/[^\p{L}\p{M}\s'.\-]/gu, '').trim().slice(0, 60);
    if (!name || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return out_({ ok: false, error: 'invalid' });
    if (!limit_('e_' + email.toLowerCase(), 3, 3600) || !limit_('day', 40, 21600)) return out_({ ok: false, error: 'rate' });

    const lang = LANGS.indexOf(d.lang) >= 0 ? d.lang : 'en';
    const din = date_(d.in), dout = date_(d.out);
    const msg = String(d.msg || '').slice(0, 2000);
    sheet_().appendRow([new Date(), lang, name, email, din, dout, num_(d.adults), num_(d.children), num_(d.dogs), String(d.total || ''), msg, String(d.page || '').slice(0, 200)]);

    MailApp.sendEmail({
      to: HOSTS, replyTo: email,
      subject: 'Booking request: ' + name + ', ' + din + ' – ' + dout,
      body: [
        'New request from casalafonte.it (' + lang.toUpperCase() + ')', '',
        'Name: ' + name, 'Email: ' + email, 'Dates: ' + din + ' – ' + dout,
        'Guests: ' + num_(d.adults) + ' adults, ' + num_(d.children) + ' children, ' + num_(d.dogs) + ' dogs',
        'Estimate shown: ' + (d.total || 'none'), '', 'Message:', msg || '(none)', '',
        'Reply to this email to answer the guest. The request is also saved in the spreadsheet.'
      ].join('\n')
    });

    const T = TPL[lang];
    MailApp.sendEmail({ to: email, replyTo: HOSTS.split(',')[0], name: 'Casa La Fonte', subject: T.subj, body: T.body(name, din, dout) });
    return out_({ ok: true });
  } catch (err) {
    console.error(err);
    return out_({ ok: false, error: 'server' });
  }
}

function doGet() { return out_({ ok: true, service: 'casa-la-fonte-requests' }); }

function out_(o) { return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON); }
function num_(v) { const n = parseInt(v, 10); return isNaN(n) ? 0 : Math.max(0, Math.min(n, 9)); }
function date_(iso) { const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(iso || '')); return m ? m[3] + '.' + m[2] + '.' + m[1] : '?'; }
function limit_(key, max, seconds) {
  const c = CacheService.getScriptCache(), n = parseInt(c.get(key) || '0', 10);
  if (n >= max) return false;
  c.put(key, String(n + 1), seconds);
  return true;
}
function sheet_() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sh = ss.getSheetByName(SHEET_NAME);
  if (!sh) {
    sh = ss.insertSheet(SHEET_NAME);
    sh.appendRow(['Received', 'Language', 'Name', 'Email', 'Arrival', 'Departure', 'Adults', 'Children', 'Dogs', 'Estimate', 'Message', 'Page']);
    sh.setFrozenRows(1);
  }
  return sh;
}

const SIGN = '\n\nDaniel & Eva\nCasa La Fonte · San Dalmazio, Toscana\nhttps://casalafonte.it';
const TPL = {
  en: { subj: 'Casa La Fonte – we have your request',
        body: (n, a, b) => 'Dear ' + n + ',\n\nThank you for your request for Casa La Fonte from ' + a + ' to ' + b + '. We will reply within a day with availability, the price and a short rental agreement.\n\nIf you have questions in the meantime, just reply to this email.' + SIGN },
  de: { subj: 'Casa La Fonte – eure Anfrage ist angekommen',
        body: (n, a, b) => 'Hallo ' + n + ',\n\nvielen Dank für eure Anfrage für die Casa La Fonte vom ' + a + ' bis ' + b + '. Wir melden uns innerhalb eines Tages mit Verfügbarkeit, Preis und einem kurzen Mietvertrag.\n\nWenn ihr in der Zwischenzeit Fragen habt, antwortet einfach auf diese E-Mail.' + SIGN },
  it: { subj: 'Casa La Fonte – abbiamo ricevuto la vostra richiesta',
        body: (n, a, b) => 'Gentile ' + n + ',\n\ngrazie per la richiesta per Casa La Fonte dal ' + a + ' al ' + b + '. Vi rispondiamo entro un giorno con disponibilità, prezzo e un breve contratto di locazione.\n\nPer qualsiasi domanda nel frattempo, basta rispondere a questa email.' + SIGN },
  nl: { subj: 'Casa La Fonte – we hebben je aanvraag ontvangen',
        body: (n, a, b) => 'Beste ' + n + ',\n\nbedankt voor je aanvraag voor Casa La Fonte van ' + a + ' tot ' + b + '. We antwoorden binnen een dag met de beschikbaarheid, de prijs en een korte huurovereenkomst.\n\nHeb je intussen vragen? Beantwoord dan gewoon deze e-mail.' + SIGN },
  da: { subj: 'Casa La Fonte – vi har modtaget jeres forespørgsel',
        body: (n, a, b) => 'Kære ' + n + ',\n\ntak for jeres forespørgsel på Casa La Fonte fra ' + a + ' til ' + b + '. Vi svarer inden for en dag med ledighed, pris og en kort lejeaftale.\n\nHar I spørgsmål i mellemtiden, så svar bare på denne e-mail.' + SIGN },
  fr: { subj: 'Casa La Fonte – nous avons bien reçu votre demande',
        body: (n, a, b) => 'Bonjour ' + n + ',\n\nmerci pour votre demande pour Casa La Fonte du ' + a + ' au ' + b + '. Nous vous répondons sous un jour avec la disponibilité, le prix et un court contrat de location.\n\nSi vous avez des questions d’ici là, répondez simplement à cet e-mail.' + SIGN }
};
