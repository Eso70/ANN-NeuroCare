export function BotanicalArtwork() {
  return <figure className="botanical-study" aria-labelledby="botanical-caption">
    <div className="botanical-index"><span>A STUDY IN PATTERNS</span><span>01 / 21</span></div>
    <svg viewBox="0 0 420 440" fill="none" role="img" aria-labelledby="botanical-title botanical-description">
      <title id="botanical-title">A quiet study of growth and connection</title><desc id="botanical-description">Original botanical linework with a few connected points. An illustration, not a visualization of model weights.</desc>
      <path d="M216 393c-9-61-16-111-5-169 8-46 27-89 23-150" stroke="#536950" strokeWidth="1.8" />
      <path d="M219 297c-73-3-105-48-98-104 65-3 107 43 98 104Z" fill="#d4dbc9" />
      <path d="M213 232c-3-72 38-122 108-130 16 64-27 116-108 130Z" fill="#bccbb8" />
      <path d="M232 141c-47-7-78-43-69-90 54 3 82 36 69 90Z" fill="#e2d7c4" />
      <path d="M214 339c54-1 87-28 93-74-50-4-92 24-93 74Z" fill="#e4e7dc" />
      <path d="m219 295-79-80m74 17 87-113m-69 20-54-71m37 271 75-60" stroke="#61755b" strokeWidth="1.1" />
      <path d="m92 148 61 14 61-43 78 70-22 121-96 40-82-101Z" stroke="#b6c0ad" strokeDasharray="2 7" />
      {[[92,148],[153,162],[214,119],[292,189],[270,310],[174,350],[92,249]].map(([x,y],index) => <g key={index}><circle cx={x} cy={y} r="4" fill="#fbfaf6" stroke="#688062" strokeWidth="1" /><circle cx={x} cy={y} r="1.2" fill="#688062" /></g>)}
      <path d="M62 358h22m-11-11v22M338 73h18m-9-9v18" stroke="#b1baa5" strokeWidth="1" />
      <ellipse cx="214" cy="406" rx="55" ry="3" fill="#e6e6dc" />
    </svg>
    <figcaption id="botanical-caption"><span>A little structure. A little uncertainty.</span><span>NEUROCARE NOTES</span></figcaption>
  </figure>
}
