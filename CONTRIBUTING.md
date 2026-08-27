# Bidra

Vet du om et norsk bug bounty- eller responsible disclosure-program som mangler, eller er noe i listen feil? Flott!

## Slik gjør du det

1. Rediger [`programs.yaml`](programs.yaml). **Ikke** rediger tabellen i `README.md` – den genereres automatisk når endringen er inne på `main`.
2. Send en pull request. Beskrivelsen av feltene står øverst i `programs.yaml`.
3. En sjekk kjører på pull requesten og sier fra hvis noe mangler eller har feil verdi.

Eksempel på en oppføring:

```yaml
- name: Oda
  url: https://oda.com
  platform: intigriti
  visibility: public
  type: bug-bounty
  program_url: https://app.intigriti.com/researcher/programs/oda/oda
  rewards: [money]
  launched: 2022-04
  source: https://medium.com/oda-product-tech/oda-is-launching-our-bug-bounty-program-8e356d5ac0d3
  source_name: Medium
```

Er et program stengt? Sett `status: closed` i stedet for å fjerne oppføringen.

Har du ikke lyst til å lage en pull request? [Opprett et issue](../../issues/new) med lenke til programmet, så fikser jeg resten.

## Hva hører hjemme i listen?

- Program hos norske selskap, eller norske datterselskap/merkevarer av utenlandske selskap (oppgi da eier som `name` og merkevaren som `unit`).
- Både betalte bug bounty-program og responsible/vulnerability disclosure-program uten dusør.
- Private program bare hvis eksistensen er offentlig kjent (`visibility: private-known`) og du kan oppgi en kilde. Er programmet hemmelig, utelat `name` og sett `visibility: undisclosed`.

## Forhåndsvise lokalt

```sh
pip install pyyaml
python3 scripts/render.py
```
