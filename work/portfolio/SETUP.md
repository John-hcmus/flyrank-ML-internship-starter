# Going live — the remaining steps

The form is built, tested and committed. Three things stand between it and a real
message in your inbox. Budget about five minutes.

## 1. Get a free access key (~2 min)

Go to **https://web3forms.com**, put your Gmail address in the "Create Access
Key" box, and submit. They email you a key that looks like
`a1b2c3d4-5e6f-7890-abcd-ef1234567890`. Click the verification link in that email.

No account, no password, no card. The free tier is 250 submissions a month.

## 2. Paste the key into the page (~30 sec)

In `docs/portfolio/index.html`, find the clearly marked line:

```html
<input type="hidden" name="access_key" value="PASTE_YOUR_WEB3FORMS_ACCESS_KEY_HERE">
```

Replace `PASTE_YOUR_WEB3FORMS_ACCESS_KEY_HERE` with your key. **Change nothing else** —
the same string appears once more, as a constant in the JavaScript further down, and
that one has to stay exactly as it is. It is what the page uses to notice the key is
still unset and show the yellow "not connected yet" warning.

Commit and push.

## 3. Merge to `main`

GitHub Pages serves `docs/` from the **`main`** branch, so the page is not public until
this branch is merged. Once it is, wait a minute or two and open:

**https://john-hcmus.github.io/flyrank-ML-internship-starter/portfolio/**

## 4. The real test — this is the actual deliverable

1. Open that URL **in a private/incognito window**, so you are testing what a stranger
   gets, not something cached.
2. Confirm there is **no yellow warning box** above the form. If there is, the key did
   not save.
3. Fill the form in as a stranger would and send it.
4. Confirm you see the **green** "your message is on its way" line.
5. **Check your Gmail.** Check spam too — the first message from a new sender often
   lands there. Mark it "not spam" so later ones arrive properly.
6. Hit **reply** on that email and confirm it addresses the sender, not Web3Forms.

Screenshot the green line and the received email. That pair is your evidence.

## Also worth doing

- **Rewrite `HOW-IT-WORKS.md` in your own voice.** It is correct and the data flow is
  right, but the brief asks for the explainer *in your own words*, and it was drafted
  with an assistant. Read it, make sure you could defend every line of it out loud, and
  say it the way you would say it. That is the part being marked.
- **The CV link is still dead.** In the header, `<a href="#" ...>CV</a>` goes nowhere.
  Point it at your CV PDF or delete the chip — a dead button on a portfolio is worse
  than one fewer link.
- Re-run the test suite any time you touch the form:
  ```
  pip install playwright && python3 work/scripts/test_contact_form.py
  ```

## If a message never arrives

| What you see | What it means |
|---|---|
| Yellow warning above the form | The key is still the placeholder. Step 2 did not save, or you did not push. |
| Red line saying "Invalid access key" | The key is wrong, or you never clicked the verification link in step 1. |
| Red line saying "Could not reach the server" | Network or ad-blocker. Try another network with the blocker off. |
| Green line, but no email | Check spam first. Then confirm the key belongs to the address you are checking. |
