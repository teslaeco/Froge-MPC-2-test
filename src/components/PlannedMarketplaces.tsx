import './plannedMarketplaces.css'

export function PlannedMarketplaces() {
  return <section className="planned-marketplaces" aria-label="Planowane integracje ze sklepami">
    <div><p className="planned-marketplaces-label">KOLEJNY ETAP</p><h2>Twoje modele. Więcej miejsc sprzedaży.</h2><p>Planowane integracje ze sklepami. Połączenia jeszcze nie są aktywne.</p></div>
    <ul>{[['Shopify','shopify.jpg'],['Amazon','amazon.png'],['eBay','ebay.png']].map(([name,file]) => <li key={name}>
      <div className={'marketplace-logo marketplace-logo-'+name.toLowerCase()}><img src={'/brands/'+file} alt={name} loading="lazy" /></div>
      <span>Planowane połączenie</span>
    </li>)}</ul>
  </section>
}
