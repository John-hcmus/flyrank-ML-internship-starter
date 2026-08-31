# How the contact form works

My portfolio used to be a page that only talked. Now it has exactly one thing that
*does* something: a contact form. You type a message, press send, and it lands in my
Gmail inbox. This is the short explanation of what sits behind that.

---

## What a backend actually is

My portfolio is a **static site**. GitHub Pages takes the files in my repo and hands
them to whoever asks. That is the whole job. It reads files out loud; it never thinks.
Ask it to send an email and it has no idea what you mean, because serving a file and
sending mail are completely different jobs.

A **backend** is the other half: someone else's computer, switched on all the time,
sitting at a known address and waiting to be asked to do things. It can do the things a
browser cannot be trusted with — keep a secret, write to a database, charge a card,
send an email.

The reason it has to be a *separate* computer comes down to secrets. Sending mail
requires a credential, and anything I ship to a browser is public: "View source" is one
keystroke away, and the network tab shows every request. A secret in the browser is not
a secret. So the credential has to live somewhere the visitor can never read, which
means a machine I control rather than a page I hand out.

I did not build that machine. I rented one. **Web3Forms** runs a backend whose only
trick is turning a form submission into an email, and the free tier covers 250
messages a month — far more than a portfolio will ever see. Writing my own would have
meant a server, a mail provider, and a bill, to end up in the same place.

---

## What my feature does

One form, three boxes: name, email, message. Press **Send message** and:

- if something is missing or malformed, it says so under that exact box and stops —
  nothing leaves the browser;
- if everything checks out, the button greys out, the status line says it is sending,
  and a moment later it turns green: *"Thanks — your message is on its way."*

The page never reloads and you never get bounced to some other site's "thank you"
screen. Meanwhile the message is in my inbox, with the sender's address set as the
reply-to, so I hit reply and it goes straight back to them.

---

## How the data flows

```
 1. VISITOR'S BROWSER          2. GITHUB PAGES              3. WEB3FORMS
    ────────────────             ──────────────                ──────────
    opens my portfolio   ──────► "here is index.html"
                         ◄──────  (a file. that's all.)

    types name, email,
    message; hits Send

    my JavaScript checks
    the three fields
      ↓ all good?

    packs them into JSON
    and POSTs it        ──────────────────────────────────►  checks my access key
                                                             checks the honeypot
                                                             writes an email
                                                                    │
                                                                    ▼
                        ◄────────────────────────────────── {"success": true}     4. MY GMAIL
    shows the green                                                                ──────────
    "on its way" line                                        sends the mail ──────► new message
                                                                                    reply-to =
                                                                                    the visitor
```

Step by step, in words:

1. **The browser gets a file.** GitHub Pages sends `index.html`. No computing has
   happened yet by anyone.
2. **The browser does the checking.** My JavaScript makes sure there is a name, a
   plausible email, and a message of at least ten characters. This is a courtesy to the
   visitor, not security — it catches typos instantly instead of after a round trip.
3. **The browser sends the data.** It bundles the fields into JSON and `POST`s them to
   `api.web3forms.com/submit`, along with my access key, which says *which mailbox* this
   belongs to.
4. **The backend does the part I can't.** Web3Forms checks the key is real, glances at
   the honeypot (below), composes an email and sends it.
5. **My inbox gets it.** With the visitor's address as reply-to.
6. **The browser hears back.** Web3Forms answers `{"success": true}`, and my JavaScript
   turns that into the green line. If it answers with an error instead, I show the
   server's actual reason rather than a generic shrug.

The important thing about that picture: **my page never touches my email account.** It
only knows how to say "here is a message, please deliver it." The credentials that can
actually send mail live on Web3Forms' servers, where no visitor can read them.

---

## Two details I had to think about

**The access key is public, and that is fine.** It is sitting in my HTML where anyone
can read it. That felt wrong until I worked out what it actually is: an *address*, not a
password. It says "put this in Tu's mailbox." It cannot read my mail, cannot send as me,
cannot touch my account. The worst someone can do with it is send me messages — which is
what the form is for. The credential that *would* be dangerous never leaves Web3Forms.

**Bots fill in forms.** There is a fourth input on the form that you cannot see: it is
parked off the left edge of the screen, fully transparent, and skipped by the tab key. No
person will ever fill it in. Automated spam scripts read the HTML rather than look at the
page, so they see a field and fill it. If it comes back filled, the submission is a bot
and gets dropped. It is a tripwire that only something non-human can trigger.

---

## What it cost

Nothing. GitHub Pages is free, Web3Forms' free tier is 250 submissions a month, and
there is no card on file anywhere. The only thing I spend is the minute it takes to
reply.
