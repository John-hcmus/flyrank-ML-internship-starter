# How the contact form works

My portfolio used to be a page that only talked about my work. Now one thing on it
actually does something: a contact form. You type a message, hit send, and it shows up
in my Gmail. This is what happens in between.

## What a backend is

My site is static. GitHub Pages takes the files sitting in my repo and hands them to
whoever asks for them. That is the whole job. It cannot send an email — serving a file
and sending an email are different jobs, and nothing in my repo is running any code.

A backend is a computer that is always on, sitting at a known address, waiting to be
asked to do something. It can do what a browser cannot: send email, write to a database,
take a payment.

It has to be a *separate* computer because of secrets. Sending email needs a credential,
and anything I put in the page is public — View Source shows it, the network tab shows
every request. A secret in the browser is not a secret. So the credential has to live on
a machine the visitor cannot read.

I did not build that machine. I rented one. **Web3Forms** does exactly one thing: take a
form submission and turn it into an email. Free up to 250 messages a month. Building my
own would have meant a server, a mail provider and a monthly bill, to end up in the same
place.

## What happens when you hit Send

1. Your browser asks GitHub Pages for my page. It sends back `index.html`. Nobody has
   computed anything yet.
2. You fill in name, email and message, and press the button.
3. **My JavaScript checks the three fields first.** Missing name, a broken email address,
   a message under ten characters — it says so under that box and stops. Nothing leaves
   your browser. This is not security; it just saves you a round trip to find out you
   made a typo.
4. If everything looks fine, the browser packs the fields into JSON and POSTs them to
   `api.web3forms.com`, along with my access key. The key tells Web3Forms whose mailbox
   this is for.
5. **Web3Forms does the part I can't.** It checks the key, checks the honeypot (below),
   writes an email and sends it.
6. It answers `{"success": true}`. My JavaScript turns that into the green line on the
   page. If it answers with an error instead, I show the reason the server actually gave,
   not a generic "something went wrong".
7. The email lands in my inbox with the sender's address set as reply-to, so I just hit
   reply.

The part worth noticing: **my page never touches my email account.** It only knows how to
say "here is a message, please deliver it."

```
BROWSER              GITHUB PAGES          WEB3FORMS            MY GMAIL
   |  asks for page      |                     |                    |
   | ------------------> |                     |                    |
   | <------------------ |  index.html         |                    |
   |                     |  (a file, no code)  |                    |
   |                                           |                    |
   |  checks the 3 fields itself                |                    |
   |  POSTs JSON + access key ----------------> |                    |
   |                                           | checks key         |
   |                                           | checks honeypot    |
   |                                           | writes the email   |
   |                                           | -----------------> | new message
   | <---------------------------------------- |                    | reply-to =
   |  {"success": true}  ->  green line        |                    | the visitor
```

## The part that confused me

The access key sits in my HTML where anyone can read it. That felt wrong until I worked
out what it actually is: **an address, not a password.** It says "put this in Tu's
mailbox." It cannot read my mail, cannot send email as me, cannot touch my account. The
worst thing a stranger can do with it is send me a message — which is the entire point of
the form. The credential that *would* be dangerous never leaves Web3Forms' servers.

I got caught by this in practice too. The placeholder string appears twice in my file:
once as the key itself, and once as a constant in the JavaScript that checks whether the
key has been set yet. The first time I ran my tests I had replaced both, so the page
decided it was still unconfigured and refused to send anything. Every test failed. The
fix was to replace only the first one — and it taught me that the check and the thing
being checked are two different pieces, even when they look identical.

## The honeypot

There is a fourth input on the form that you cannot see. It sits off the left edge of the
screen, it is transparent, and the tab key skips over it. No person will ever type in it.
Spam bots read the HTML instead of looking at the page, so they see a field and fill it
in. If it comes back filled, the message is from a bot and gets dropped. It is a tripwire
only a machine can trip.

## What it cost

Nothing. GitHub Pages is free, Web3Forms is free up to 250 messages a month, and there is
no card on file anywhere. The only thing I spend is the minute it takes to reply.
