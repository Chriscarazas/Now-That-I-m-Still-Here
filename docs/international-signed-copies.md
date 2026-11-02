# International signed-copy orders

Reviewed 2026-11-02. No live merchant settings were changed and no payment was submitted.

## Evidence and limits

- CNAME is chriscarazas.com; the live /buy/ page matches this repository.
- Signed copies use https://square.link/u/UWKF2PAf, redirecting to Square hosted checkout for merchant ML9YW9EETGHPW. Lulu and Books2Read are separate purchase routes, not the signed-copy checkout.
- Checkout displayed $19.99 plus $5 Standard Shipping. South Africa is present and selectable in both the shipping-country and phone-country lists. There is no website-side country allowlist, checkout API, or payment integration to patch.
- Selecting South Africa alone did not show a country error. Shipping methods require a full valid address. No customer address or payment data was entered. Thus neither delivery eligibility nor successful payment to South Africa has been proven.
- Square's documentation says Payment Links support international sales but international tax and shipping-fee settings cannot be applied. Square accepts most internationally issued cards; a seller-country limitation is not a blanket ban on overseas buyers.
- No Square merchant connector or authenticated dashboard was available. The exact shipping profile, country exclusions, risk settings, and failed-payment reason remain unverified. A phone-country option does not prove shipping coverage.

## Safe website mitigation

The Buy page now offers an email enquiry for international delivery, explicitly including South Africa, before payment. It requests only country, postal code, and quantity, and asks readers not to send card details. Other signed-copy CTAs lead to that page. Existing Square checkout remains available. This enables a quote request, not automatic international checkout or a promise of worldwide delivery. The owner must confirm fulfillment and arrange a reviewed payment request including postage.

## Merchant review required before enabling automatic international sales

1. In Square Dashboard, identify the payment link above and verify its item, location, required custom field (currently labeled only “Required*”), shipping-address collection, and fulfillment configuration.
2. Review Payment links > Settings and Account & Settings > Fulfillment methods > Shipment. Confirm shipping profiles, supported destinations, South Africa coverage, and actual postage. Determine what the observed $5 charge represents; do not assume it covers international delivery.
3. Because Payment Links have international shipping/tax limitations, confirm with Square whether the current link can support the intended fulfillment. Consider a separately reviewed Square Online international shipping setup or a manually quoted order/payment request. Do not simply remove shipping collection or enable every destination.
4. Confirm carrier service to the destination, tracking, postage, customs information, duties/taxes treatment, delivery estimate, and return policy before quoting or accepting payment.
5. For an actual failed order, inspect the error and Square payment/risk logs privately. If it is an issuer decline, confirm international online purchases with the issuer; do not collect card details by email or put them in GitHub.
6. After explicit review of merchant changes, verify a complete South Africa address and another intended overseas destination produce valid fulfillment and the agreed total. Verify a US address still works. Use supported test facilities; do not submit a live charge without separate authorization.

## Sources

- https://squareup.com/help/us/en/article/6692-get-started-with-square-checkout-links
- https://squareup.com/help/us/en/article/8364-customize-square-payment-links
- https://squareup.com/help/us/en/article/5085-accepted-cards
