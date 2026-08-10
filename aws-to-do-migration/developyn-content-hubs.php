<?php
/**
 * Plugin Name: Developyn Content Hubs
 * Description: Modern industry directory and editorial news hub.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

add_shortcode( 'developyn_industries', 'developyn_render_industries_hub' );
add_shortcode( 'developyn_insights', 'developyn_render_insights_hub' );
add_shortcode( 'developyn_industry_education', 'developyn_render_education_industry' );
add_shortcode( 'developyn_industry_page', 'developyn_render_industry_page' );

function developyn_industry_page_ids() {
	return array( 9634, 9664, 9668, 9671, 9677, 9683, 9690, 9693, 9697, 9700, 10006, 10012, 10106, 10111, 10219, 10225, 10301, 10307 );
}

function developyn_is_content_hub() {
	return is_page( array_merge( array( 10020, 5833 ), developyn_industry_page_ids() ) );
}

add_filter(
	'render_block_core/post-title',
	static function ( $content ) {
		return is_page( developyn_industry_page_ids() ) ? '' : $content;
	}
);

add_action(
	'wp',
	static function () {
		if ( developyn_is_content_hub() ) {
			remove_filter( 'the_content', 'display_rich_snippet', 90 );
		}
	}
);

add_action(
	'wp_enqueue_scripts',
	static function () {
		if ( ! developyn_is_content_hub() ) {
			return;
		}

		foreach ( array( 'rating_style', 'bsf_style', 'font-awesome-svg-styles', 'font-awesome-official', 'font-awesome-official-v4shim' ) as $handle ) {
			wp_dequeue_style( $handle );
		}
		wp_dequeue_script( 'jquery_rating' );
	},
	PHP_INT_MAX
);

function developyn_render_hub_styles() {
	static $rendered = false;

	if ( $rendered ) {
		return '';
	}

	$rendered = true;
	ob_start();
	?>
	<style id="developyn-content-hubs-css">
		.developyn-hub{--hub-bg:#191b1d;--hub-panel:#202326;--hub-panel-2:#25292d;--hub-border:#363d43;--hub-muted:#a9b1b8;--hub-accent:#1fa5d9;--hub-accent-soft:#8edcf8;--hub-text:#f7f8f8;box-sizing:border-box;color:var(--hub-text);width:min(100%,1280px);margin:0 auto;padding:clamp(2rem,5vw,5rem) clamp(1rem,3vw,2rem) 5rem;font-family:"Space Grotesk",sans-serif}
		.developyn-hub *{box-sizing:border-box}
		.developyn-hub [hidden]{display:none!important}
		.page-id-10020 .navburger:before,.page-id-5833 .navburger:before{content:"\2630";font-family:Arial,sans-serif;font-size:1.4em;line-height:1}
		.developyn-hub a{color:inherit}
		.developyn-hub__hero{position:relative;isolation:isolate;overflow:hidden;padding:clamp(2rem,6vw,5.5rem);border:1px solid var(--hub-border);border-radius:28px;background:radial-gradient(circle at 88% 16%,rgba(31,165,217,.25),transparent 31%),linear-gradient(135deg,#252a2e 0%,#191b1d 64%)}
		.developyn-hub__hero:after{content:"";position:absolute;z-index:-1;inset:0;background-image:linear-gradient(rgba(255,255,255,.025) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.025) 1px,transparent 1px);background-size:38px 38px;mask-image:linear-gradient(to left,#000,transparent 78%)}
		.developyn-hub__eyebrow{display:flex;align-items:center;gap:.65rem;margin:0 0 1rem;color:var(--hub-accent-soft);font-size:.77rem;font-weight:700;letter-spacing:.16em;text-transform:uppercase}
		.developyn-hub__eyebrow:before{content:"";width:2rem;height:2px;background:var(--hub-accent)}
		.developyn-hub__hero h1{max-width:900px;margin:0;color:var(--hub-text);font-family:"Space Grotesk",sans-serif!important;font-size:clamp(2.75rem,7vw,6.4rem);font-weight:500;letter-spacing:-.055em;line-height:.94}
		.developyn-hub__hero-copy{max-width:740px;margin:1.5rem 0 0;color:#d5dade;font-size:clamp(1.05rem,1.7vw,1.3rem);line-height:1.65}
		.developyn-hub__signals{display:flex;flex-wrap:wrap;gap:.65rem;margin:2rem 0 0;padding:0;list-style:none}
		.developyn-hub__signals li{padding:.6rem .85rem;border:1px solid #465058;border-radius:999px;background:rgba(17,19,20,.5);color:#e7eaec;font-size:.85rem}
		.developyn-hub__section{margin-top:clamp(3rem,7vw,6rem)}
		.developyn-hub__section-head{display:flex;align-items:end;justify-content:space-between;gap:2rem;margin-bottom:1.5rem}
		.developyn-hub__section-head h2{margin:0;color:var(--hub-text);font-size:clamp(1.9rem,4vw,3.25rem);font-weight:500;letter-spacing:-.035em;line-height:1.05}
		.developyn-hub__section-head p{max-width:520px;margin:0;color:var(--hub-muted);line-height:1.6}
		.developyn-hub__filter-shell{position:sticky;z-index:6;top:1rem;padding:.75rem;border:1px solid var(--hub-border);border-radius:18px;background:rgba(25,27,29,.92);box-shadow:0 12px 40px rgba(0,0,0,.2);backdrop-filter:blur(14px)}
		.developyn-hub__filters{display:flex;gap:.55rem;overflow-x:auto;scrollbar-width:none}
		.developyn-hub__filters::-webkit-scrollbar{display:none}
		.developyn-hub__filter{flex:0 0 auto;padding:.7rem 1rem;border:1px solid transparent;border-radius:12px;background:transparent;color:#c7cdd1;font:inherit;font-size:.86rem;font-weight:600;cursor:pointer;transition:.2s ease}
		.developyn-hub__filter:hover,.developyn-hub__filter:focus-visible{border-color:#4a545b;color:#fff;outline:none}
		.developyn-hub__filter[aria-pressed="true"]{background:var(--hub-accent);color:#07171d}
		.developyn-hub__count{margin:1rem 0 1.25rem;color:var(--hub-muted);font-size:.85rem}
		.developyn-industries__grid,.developyn-insights__grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:1.1rem}
		.developyn-industry-card{position:relative;display:flex;min-height:100%;overflow:hidden;border:1px solid var(--hub-border);border-radius:20px;background:linear-gradient(160deg,var(--hub-panel-2),var(--hub-panel));text-decoration:none;transition:transform .25s ease,border-color .25s ease,box-shadow .25s ease}
		.developyn-industry-card:hover,.developyn-industry-card:focus-visible{z-index:1;transform:translateY(-5px);border-color:rgba(31,165,217,.85);box-shadow:0 20px 45px rgba(0,0,0,.3);outline:none}
		.developyn-industry-card__media{position:absolute;inset:0;margin:0}
		.developyn-industry-card__media:after{content:"";position:absolute;inset:0;background:linear-gradient(to top,rgba(17,19,20,.98) 8%,rgba(17,19,20,.76) 48%,rgba(17,19,20,.08) 100%)}
		.developyn-industry-card__media img{width:100%;height:100%;object-fit:cover;transition:transform .5s ease}
		.developyn-industry-card:hover img{transform:scale(1.035)}
		.developyn-industry-card__body{position:relative;z-index:1;display:flex;flex-direction:column;min-height:430px;width:100%;padding:1.35rem;justify-content:flex-end}
		.developyn-industry-card__sector{margin-bottom:.6rem;color:var(--hub-accent-soft);font-size:.7rem;font-weight:700;letter-spacing:.13em;text-transform:uppercase}
		.developyn-industry-card h3{margin:0;color:#fff;font-size:clamp(1.35rem,2vw,1.75rem);font-weight:500;letter-spacing:-.025em;line-height:1.08}
		.developyn-industry-card p{margin:.7rem 0 1.2rem;color:#d2d7da;font-size:.92rem;line-height:1.55}
		.developyn-industry-card__link{display:flex;align-items:center;justify-content:space-between;padding-top:1rem;border-top:1px solid rgba(255,255,255,.16);color:#fff;font-size:.82rem;font-weight:700}
		.developyn-industry-card__link span:last-child{color:var(--hub-accent);font-size:1.2rem;transition:transform .2s ease}
		.developyn-industry-card:hover .developyn-industry-card__link span:last-child{transform:translateX(4px)}
		.developyn-hub__cta{display:grid;grid-template-columns:1.35fr auto;align-items:center;gap:2rem;margin-top:clamp(3rem,7vw,6rem);padding:clamp(1.5rem,4vw,3.5rem);border:1px solid #3d5a66;border-radius:24px;background:linear-gradient(115deg,#17303a,#20272b 62%)}
		.developyn-hub__cta h2{margin:0 0 .55rem;color:#fff;font-size:clamp(1.7rem,3vw,2.65rem);font-weight:500;letter-spacing:-.035em}
		.developyn-hub__cta p{margin:0;color:#c5d0d5;line-height:1.6}
		.developyn-hub__button{display:inline-flex;align-items:center;justify-content:center;min-height:48px;padding:.8rem 1.15rem;border:1px solid var(--hub-accent);border-radius:12px;background:var(--hub-accent);color:#07171d!important;font-weight:700;text-decoration:none;white-space:nowrap;transition:.2s ease}
		.developyn-hub__button:hover,.developyn-hub__button:focus-visible{transform:translateY(-2px);box-shadow:0 10px 28px rgba(31,165,217,.25);outline:none}
		.developyn-insights__tools{display:grid;grid-template-columns:1fr minmax(260px,390px);gap:1rem;align-items:center;margin:2rem 0}
		.developyn-insights__topics{display:flex;gap:.5rem;overflow-x:auto;scrollbar-width:none}
		.developyn-insights__topic{flex:0 0 auto;padding:.62rem .85rem;border:1px solid var(--hub-border);border-radius:999px;color:#cbd1d5;text-decoration:none;font-size:.8rem;font-weight:600}
		.developyn-insights__topic[aria-current="page"],.developyn-insights__topic:hover{border-color:var(--hub-accent);background:rgba(31,165,217,.12);color:#fff}
		.developyn-insights__search{display:flex;gap:.5rem;padding:.45rem;border:1px solid var(--hub-border);border-radius:14px;background:var(--hub-panel)}
		.developyn-insights__search input{min-width:0;width:100%;padding:.6rem .75rem;border:0;background:transparent;color:#fff;font:inherit;outline:none}
		.developyn-insights__search input::placeholder{color:#858e95}
		.developyn-insights__search button{padding:.62rem .9rem;border:0;border-radius:10px;background:var(--hub-accent);color:#07171d;font:inherit;font-size:.82rem;font-weight:700;cursor:pointer}
		.developyn-insights__lead-grid{display:grid;grid-template-columns:1.45fr .75fr;gap:1.1rem;margin-bottom:1.1rem}
		.developyn-insights__secondary{display:grid;gap:1.1rem}
		.developyn-insight-card{height:100%;overflow:hidden;border:1px solid var(--hub-border);border-radius:20px;background:var(--hub-panel);transition:transform .25s ease,border-color .25s ease}
		.developyn-insight-card:hover{transform:translateY(-4px);border-color:#52616a}
		.developyn-insight-card>a{display:flex;height:100%;flex-direction:column;text-decoration:none}
		.developyn-insight-card__media{position:relative;display:block;aspect-ratio:16/9;overflow:hidden;background:radial-gradient(circle at 78% 20%,rgba(111,218,255,.38),transparent 25%),linear-gradient(135deg,#153847,#236a82)}
		.developyn-insight-card__media img{width:100%;height:100%;object-fit:cover;transition:transform .45s ease}
		.developyn-insight-card:hover img{transform:scale(1.035)}
		.developyn-insight-card__fallback{position:absolute;inset:0;display:flex;align-items:flex-end;padding:1.25rem;color:rgba(255,255,255,.72);font-size:.72rem;font-weight:700;letter-spacing:.15em;text-transform:uppercase}
		.developyn-insight-card__fallback:before{content:"";position:absolute;top:18%;right:10%;width:30%;aspect-ratio:1;border:1px solid rgba(255,255,255,.28);border-radius:50%;box-shadow:-45px 34px 0 -1px transparent,-45px 34px 0 0 rgba(255,255,255,.16)}
		.developyn-insight-card__body{display:flex;flex:1;flex-direction:column;padding:1.2rem}
		.developyn-insight-card__meta{display:flex;align-items:center;gap:.55rem;margin-bottom:.7rem;color:var(--hub-accent-soft);font-size:.7rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase}
		.developyn-insight-card__meta time{color:#9ba4aa;font-weight:500;letter-spacing:0;text-transform:none}
		.developyn-insight-card h2{margin:0;color:#fff;font-size:1.25rem;font-weight:500;letter-spacing:-.025em;line-height:1.2}
		.developyn-insight-card p{display:-webkit-box;margin:.75rem 0 1rem;overflow:hidden;color:#bac2c7;font-size:.88rem;line-height:1.55;-webkit-box-orient:vertical;-webkit-line-clamp:3}
		.developyn-insight-card__read{margin-top:auto;color:#fff;font-size:.78rem;font-weight:700}
		.developyn-insight-card--featured .developyn-insight-card__media{aspect-ratio:16/8.1}
		.developyn-insight-card--featured .developyn-insight-card__body{padding:clamp(1.25rem,3vw,2rem)}
		.developyn-insight-card--featured h2{font-size:clamp(1.8rem,3.3vw,3rem);line-height:1.05}
		.developyn-insight-card--featured p{max-width:720px;font-size:1rem}
		.developyn-insight-card--compact{min-height:0}
		.developyn-insight-card--compact>a{display:grid;grid-template-columns:34% 1fr}
		.developyn-insight-card--compact .developyn-insight-card__media{height:100%;aspect-ratio:auto}
		.developyn-insight-card--compact .developyn-insight-card__body{padding:1rem}
		.developyn-insight-card--compact h2{font-size:1.2rem;line-height:1.18}
		.developyn-insight-card--compact p{display:none}
		.developyn-insights__results{margin:0 0 1rem;color:var(--hub-muted);font-size:.85rem}
		.developyn-insights__empty{padding:3rem;border:1px dashed #4b555c;border-radius:18px;text-align:center;color:var(--hub-muted)}
		.developyn-insights__pagination{display:flex;flex-wrap:wrap;gap:.5rem;justify-content:center;margin-top:2.5rem}
		.developyn-insights__pagination .page-numbers{display:grid;min-width:42px;height:42px;padding:0 .7rem;place-items:center;border:1px solid var(--hub-border);border-radius:10px;color:#d5dade;text-decoration:none}
		.developyn-insights__pagination .current,.developyn-insights__pagination a:hover{border-color:var(--hub-accent);background:var(--hub-accent);color:#07171d}
		.developyn-hub__sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}
		.developyn-sector__breadcrumb{display:flex;gap:.5rem;margin:0 0 1.25rem;color:var(--hub-muted);font-size:.78rem}
		.developyn-sector__breadcrumb a{text-decoration:none}
		.developyn-sector__breadcrumb a:hover{text-decoration:underline}
		.developyn-sector__hero{display:grid;grid-template-columns:minmax(0,1.05fr) minmax(340px,.75fr);gap:clamp(1.5rem,4vw,4rem);align-items:end;padding:clamp(1.5rem,4vw,3.5rem);border:1px solid var(--hub-border);border-radius:28px;background:linear-gradient(145deg,#242a2e,#181a1c 72%)}
		.developyn-sector__hero h1{max-width:760px;margin:0;color:#fff;font-size:clamp(2.7rem,6.3vw,5.8rem);font-weight:500;letter-spacing:-.055em;line-height:.94}
		.developyn-sector__hero-copy{max-width:680px;margin:1.35rem 0 0;color:#cbd2d6;font-size:clamp(1rem,1.5vw,1.2rem);line-height:1.65}
		.developyn-sector__actions{display:flex;flex-wrap:wrap;gap:.7rem;margin-top:1.7rem}
		.developyn-sector__text-link{display:inline-flex;align-items:center;min-height:48px;padding:.8rem 1rem;border:1px solid #4a555c;border-radius:12px;color:#fff;text-decoration:none;font-weight:700}
		.developyn-sector__visual{position:relative;min-height:480px;overflow:hidden;border-radius:20px;background:#17303a}
		.developyn-sector__visual img{position:absolute;width:100%;height:100%;object-fit:cover}
		.developyn-sector__visual:after{content:"";position:absolute;inset:0;background:linear-gradient(to top,rgba(14,17,19,.8),transparent 55%)}
		.developyn-sector__visual-note{position:absolute;z-index:1;right:1rem;bottom:1rem;left:1rem;padding:1rem;border:1px solid rgba(255,255,255,.2);border-radius:14px;background:rgba(17,21,23,.72);color:#eef1f2;font-size:.78rem;font-weight:700;letter-spacing:.04em;backdrop-filter:blur(10px)}
		.developyn-sector__intro{display:grid;grid-template-columns:minmax(0,.85fr) minmax(0,1.15fr);gap:clamp(2rem,7vw,7rem);align-items:start}
		.developyn-sector__intro h2{margin:0;color:#fff;font-size:clamp(2rem,4.5vw,3.8rem)!important;font-weight:500;letter-spacing:-.045em;line-height:1.02}
		.developyn-sector__intro-copy{padding-top:.4rem;color:#c1c9cd;font-size:1.05rem;line-height:1.75}
		.developyn-sector__intro-copy p{margin:0 0 1rem}
		.developyn-sector__solution-grid{display:grid;grid-template-columns:repeat(12,minmax(0,1fr));gap:1rem}
		.developyn-sector__solution{grid-column:span 4;min-height:280px;padding:1.4rem;border:1px solid var(--hub-border);border-radius:20px;background:linear-gradient(155deg,#272c30,#1e2124)}
		.developyn-sector__solution:nth-child(1),.developyn-sector__solution:nth-child(2){grid-column:span 6}
		.developyn-sector__number{display:block;margin-bottom:3.5rem;color:var(--hub-accent-soft);font-size:.72rem;font-weight:700;letter-spacing:.14em}
		.developyn-sector__solution h3{margin:0;color:#fff;font-size:1.35rem;font-weight:500;letter-spacing:-.025em}
		.developyn-sector__solution p{margin:.7rem 0 0;color:#b8c0c5;font-size:.91rem;line-height:1.6}
		.developyn-sector__solution a{color:var(--hub-accent-soft);text-underline-offset:3px}
		.developyn-sector__outcomes{display:grid;grid-template-columns:minmax(0,.75fr) minmax(0,1.25fr);gap:1rem}
		.developyn-sector__outcome-lead{display:flex;min-height:100%;flex-direction:column;justify-content:space-between;padding:clamp(1.5rem,4vw,3rem);border:1px solid #3d5a66;border-radius:22px;background:linear-gradient(145deg,#163641,#20272b)}
		.developyn-sector__outcome-lead h2{margin:0;color:#fff;font-size:clamp(2rem,4vw,3.6rem)!important;font-weight:500;letter-spacing:-.045em;line-height:1.03}
		.developyn-sector__outcome-lead p{margin:2rem 0 0;color:#c5d0d5;line-height:1.65}
		.developyn-sector__outcome-list{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:1rem;margin:0;padding:0;list-style:none}
		.developyn-sector__outcome-list li{padding:1.4rem;border:1px solid var(--hub-border);border-radius:18px;background:var(--hub-panel);color:#bfc7cb;line-height:1.55}
		.developyn-sector__outcome-list strong{display:block;margin-bottom:.55rem;color:#fff;font-size:1.05rem;font-weight:500}
		.developyn-sector__proof{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:1rem;margin-top:1rem}
		.developyn-sector__proof-item{padding:1.35rem;border:1px solid #3d5a66;border-radius:18px;background:#192c34}
		.developyn-sector__proof-item strong{display:block;margin-bottom:.45rem;color:var(--hub-accent-soft);font-size:clamp(1.25rem,2.4vw,2rem);font-weight:500;letter-spacing:-.025em}
		.developyn-sector__proof-item span{color:#c5d0d5;font-size:.87rem;line-height:1.5}
		.developyn-sector__process{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:1rem;counter-reset:sector-step}
		.developyn-sector__step{position:relative;padding:1.5rem 1.5rem 1.5rem 4.5rem;border-top:1px solid #4a555c;counter-increment:sector-step}
		.developyn-sector__step:before{content:"0" counter(sector-step);position:absolute;top:1.5rem;left:0;color:var(--hub-accent-soft);font-size:.78rem;font-weight:700;letter-spacing:.1em}
		.developyn-sector__step h3{margin:0 0 .6rem;color:#fff;font-size:1.2rem;font-weight:500}
		.developyn-sector__step p{margin:0;color:#aeb7bc;font-size:.9rem;line-height:1.6}
		.developyn-sector .developyn-hub__section-head{align-items:start}
		.developyn-sector .developyn-hub__section-head h2{font-size:clamp(1.9rem,4vw,3.25rem)!important}
		.developyn-sector .developyn-hub__cta h2{font-size:clamp(1.7rem,3vw,2.65rem)!important}
		@media(max-width:900px){.developyn-industries__grid,.developyn-insights__grid{grid-template-columns:repeat(2,minmax(0,1fr))}.developyn-insights__lead-grid{grid-template-columns:1fr}.developyn-insights__secondary{grid-template-columns:repeat(2,minmax(0,1fr))}.developyn-insights__tools{grid-template-columns:1fr}.developyn-hub__cta{grid-template-columns:1fr}.developyn-hub__cta .developyn-hub__button{justify-self:start}.developyn-hub__section-head{display:block}.developyn-hub__section-head p{margin-top:.8rem}}
		@media(max-width:900px){.developyn-sector__hero,.developyn-sector__intro,.developyn-sector__outcomes{grid-template-columns:1fr}.developyn-sector__visual{min-height:420px}.developyn-sector__solution,.developyn-sector__solution:nth-child(1),.developyn-sector__solution:nth-child(2){grid-column:span 6}}
		@media(max-width:620px){.developyn-hub{padding-inline:.75rem}.developyn-hub__hero{padding:2rem 1.25rem;border-radius:20px}.developyn-hub__hero h1{font-size:clamp(2.5rem,14vw,4rem)}.developyn-hub__signals{gap:.4rem}.developyn-hub__signals li{font-size:.72rem}.developyn-hub__filter-shell{position:static;margin-inline:-.15rem}.developyn-industries__grid,.developyn-insights__grid,.developyn-insights__secondary{grid-template-columns:1fr}.developyn-industry-card__body{min-height:380px}.developyn-insights__tools{margin-top:1.25rem}.developyn-insight-card--compact>a{grid-template-columns:34% 1fr}.developyn-insight-card--compact h2{font-size:1.05rem}.developyn-hub__cta{border-radius:18px}.developyn-sector__hero{padding:1.25rem;border-radius:20px}.developyn-sector__hero h1{font-size:clamp(2.55rem,13.5vw,4rem)}.developyn-sector__visual{min-height:350px}.developyn-sector__solution,.developyn-sector__solution:nth-child(1),.developyn-sector__solution:nth-child(2){grid-column:1/-1;min-height:0}.developyn-sector__number{margin-bottom:2.5rem}.developyn-sector__outcome-list,.developyn-sector__process,.developyn-sector__proof{grid-template-columns:1fr}}
	</style>
	<?php
	return ob_get_clean();
}

function developyn_industries_data() {
	return array(
		array( 'title' => 'Automotive', 'sector' => 'industrial', 'sector_label' => 'Industrial & logistics', 'image' => '/wp-content/uploads/2025/10/Automotive-1024x556.jpg', 'url' => '/automotive/', 'summary' => 'Connected tools for production, fleet operations, aftermarket services and customer journeys.' ),
		array( 'title' => 'Construction & Property', 'sector' => 'built', 'sector_label' => 'Built environment', 'image' => '/wp-content/uploads/2025/10/Construction-and-Property-Industry-1024x556.webp', 'url' => '/construction-and-property/', 'summary' => 'Site reporting, contractor coordination and operational visibility built around real projects.' ),
		array( 'title' => 'Education & Training', 'sector' => 'people', 'sector_label' => 'People & services', 'image' => '/wp-content/uploads/2025/10/Education-Training-Industry-1024x556.jpg', 'url' => '/education-and-training/', 'summary' => 'Learning platforms and training systems that engage users and reduce administration.' ),
		array( 'title' => 'Engineering', 'sector' => 'industrial', 'sector_label' => 'Industrial & logistics', 'image' => '/wp-content/uploads/2025/10/Engineering-1024x556.webp', 'url' => '/engineering-software-solutions/', 'summary' => 'Planning, production and reporting software for complex engineering workflows.' ),
		array( 'title' => 'Environmental & Nonprofits', 'sector' => 'regulated', 'sector_label' => 'Regulated & specialist', 'image' => '/wp-content/uploads/2025/10/Environmental-1024x556.jpg', 'url' => '/environmental-and-nonprofits/', 'summary' => 'Practical digital tools that help purpose-led organisations extend their impact.' ),
		array( 'title' => 'Enterprise Resource Planning', 'sector' => 'regulated', 'sector_label' => 'Regulated & specialist', 'image' => '/wp-content/uploads/2025/11/Enterprise-Resource-Planning-1024x556.jpg', 'url' => '/enterprise-resource-planning-software/', 'summary' => 'Integrated systems that connect data, simplify processes and support better decisions.' ),
		array( 'title' => 'Fitness & Recreation', 'sector' => 'people', 'sector_label' => 'People & services', 'image' => '/wp-content/uploads/2025/10/Fitness-1024x556.jpg', 'url' => '/fitness-and-recreation/', 'summary' => 'Member experiences, booking platforms and mobile products that keep communities engaged.' ),
		array( 'title' => 'Health & Safety', 'sector' => 'built', 'sector_label' => 'Built environment', 'image' => '/wp-content/uploads/2026/01/healthsafety-1024x538.jpg', 'url' => '/health-and-safety-software/', 'summary' => 'Digital inspections, incident reporting and audit trails that make compliance easier.' ),
		array( 'title' => 'Hospitality', 'sector' => 'people', 'sector_label' => 'People & services', 'image' => '/wp-content/uploads/2025/12/hospitality-1024x538.jpg', 'url' => '/hospitality-software/', 'summary' => 'Joined-up operations for venues, hospitality groups and customer-facing teams.' ),
		array( 'title' => 'Human Resources', 'sector' => 'people', 'sector_label' => 'People & services', 'image' => '/wp-content/uploads/2025/10/Human-Resources-1024x556.jpg', 'url' => '/human-resource-management-software/', 'summary' => 'Secure employee workflows that reduce administration and improve team visibility.' ),
		array( 'title' => 'Insurance', 'sector' => 'regulated', 'sector_label' => 'Regulated & specialist', 'image' => '/wp-content/uploads/2025/12/insurance-1024x538.jpg', 'url' => '/insurance-software/', 'summary' => 'Purpose-built platforms for brokers, insurers, underwriting and policy operations.' ),
		array( 'title' => 'Legal', 'sector' => 'regulated', 'sector_label' => 'Regulated & specialist', 'image' => '/wp-content/uploads/2026/01/legal-1024x538.jpg', 'url' => '/legal-industry-software/', 'summary' => 'Accurate, secure systems for matters, contracts, evidence and compliance workflows.' ),
		array( 'title' => 'Logistics', 'sector' => 'industrial', 'sector_label' => 'Industrial & logistics', 'image' => '/wp-content/uploads/2025/11/Logistics-1024x556.jpg', 'url' => '/logistics-software/', 'summary' => 'Real-time operational tools for supply chains, tracking and multi-team coordination.' ),
		array( 'title' => 'Manufacturing', 'sector' => 'industrial', 'sector_label' => 'Industrial & logistics', 'image' => '/wp-content/uploads/2025/10/Manufacturing-1024x556.jpg', 'url' => '/manufacturing/', 'summary' => 'Production visibility, process control and connected data from floor to boardroom.' ),
		array( 'title' => 'MedTech & Healthcare', 'sector' => 'regulated', 'sector_label' => 'Regulated & specialist', 'image' => '/wp-content/uploads/2025/10/MedTech-1024x556.webp', 'url' => '/medtech-and-healthcare/', 'summary' => 'Reliable digital products designed around privacy, evidence and safer outcomes.' ),
		array( 'title' => 'Retail & Ecommerce', 'sector' => 'regulated', 'sector_label' => 'Regulated & specialist', 'image' => '/wp-content/uploads/2025/10/Retail-1024x556.jpg', 'url' => '/retail-and-e-commerce-software-solutions/', 'summary' => 'Connected commerce experiences spanning customers, inventory and internal operations.' ),
		array( 'title' => 'Travel', 'sector' => 'people', 'sector_label' => 'People & services', 'image' => '/wp-content/uploads/2025/10/Travel-1024x556.jpg', 'url' => '/travel-management-system-development/', 'summary' => 'Booking, compliance and management workflows that make business travel easier.' ),
		array( 'title' => 'Utilities & Energy', 'sector' => 'industrial', 'sector_label' => 'Industrial & logistics', 'image' => '/wp-content/uploads/2025/10/Utilities-1024x556.jpg', 'url' => '/utilities-and-energy-sector/', 'summary' => 'Resilient platforms for field operations, infrastructure data and real-time decisions.' ),
	);
}

function developyn_industry_pages_data() {
	return array(
		'automotive' => array(
			'label' => 'Automotive',
			'headline' => 'Software that keeps automotive operations moving.',
			'hero' => 'Connect production, fleet, aftermarket and retail workflows with software designed around the way your automotive business operates.',
			'image' => '/wp-content/uploads/2025/10/Automotive.jpg',
			'note' => 'Production / Fleet / Aftermarket / Retail',
			'intro_title' => 'Drive change without disrupting the operation.',
			'intro' => array( 'Automotive teams manage complex products, fast-moving service expectations and data spread across multiple systems.', 'We build scalable tools that reduce manual work, surface real-time insight and connect cleanly with the platforms your teams already depend on.' ),
			'solutions' => array(
				array( '01 / FLOW', 'Production management', 'Plan work, track jobs and make production progress visible across teams.' ),
				array( '02 / SERVICE', 'Aftermarket platforms', 'Bring inventory, bookings and service activity into one dependable workflow.' ),
				array( '03 / MOBILE', 'Driver and team apps', 'Cross-platform mobile experiences for field teams, customers and operational users.', '/services/mobile-app-development/', 'Explore mobile development' ),
				array( '04 / INSIGHT', 'Operational dashboards', 'Turn live production, service and fleet data into faster decisions.' ),
				array( '05 / CONNECT', 'ERP and CRM integration', 'Connect enterprise systems and specialist automotive databases without duplicating work.' ),
			),
			'outcome_heading' => 'Built around the whole automotive journey.',
			'outcome_copy' => 'From the factory floor to the customer relationship, the strongest systems fit existing people and processes while creating room to grow.',
			'outcomes' => array(
				array( 'Less manual work', 'Automate repetitive administration and reduce service friction.' ),
				array( 'Real-time decisions', 'Give teams a current view of jobs, performance and exceptions.' ),
				array( 'Connected operations', 'Move data reliably between ERP, CRM and specialist platforms.' ),
				array( 'Scalable architecture', 'Adapt as products, locations and market demands change.' ),
				array( 'End-to-end delivery', 'Bring web, mobile and backend expertise into one delivery team.' ),
			),
			'cta' => 'Where could connected software remove friction from your automotive operation?',
		),
		'construction-and-property' => array(
			'label' => 'Construction & property',
			'headline' => 'Build with clearer data from site to boardroom.',
			'hero' => 'Replace paper-heavy processes with connected tools for sites, contractors, compliance, reporting and property operations.',
			'image' => '/wp-content/uploads/2025/10/Construction-and-Property-Industry.jpg',
			'note' => 'Site operations / Compliance / Property / Reporting',
			'intro_title' => 'Practical software for work that happens on site.',
			'intro' => array( 'Construction and property teams need accurate information across changing sites, suppliers and project stakeholders.', 'We create field-ready platforms that centralise records, improve visibility and integrate with the systems already supporting your projects.' ),
			'solutions' => array(
				array( '01 / PROJECTS', 'Project and compliance systems', 'Coordinate procurement, logistics, records and compliance from one secure platform.', '/services/bespoke-software-development/', 'Explore bespoke software' ),
				array( '02 / FIELD', 'Mobile site applications', 'Give field teams dependable inspections, updates and evidence capture on phones and tablets.' ),
				array( '03 / INSIGHT', 'Dashboards and reporting', 'Track KPIs, finances, delivery and compliance across one site or many.' ),
				array( '04 / PROPERTY', 'CRM and property tools', 'Connect customer, project and property-management workflows without duplicated data.' ),
				array( '05 / SAFETY', 'Contractor induction', 'Digitise inductions, safety reporting and audit-ready contractor records.', '/services/contractor-induction-software-development/', 'Explore induction software' ),
			),
			'proof' => array( array( '100,000+', 'Subcontractors inducted through the TSL platform.' ), array( '< 15 min', 'TSL induction time, reduced from one to two hours.' ), array( '75%+', 'Reduction in induction time achieved for Castlemore Homes.' ) ),
			'outcome_heading' => 'Make every site easier to see and manage.',
			'outcome_copy' => 'The right platform replaces fragmented spreadsheets and paper records with live information your site and office teams can trust.',
			'outcomes' => array(
				array( 'Multi-site visibility', 'See activity, risk and progress without waiting for manual reports.' ),
				array( 'Audit-ready records', 'Centralise inductions, evidence and compliance history.' ),
				array( 'Connected systems', 'Integrate legacy tools and cloud platforms for consistent data flow.' ),
				array( 'Field-first experience', 'Make important workflows straightforward on site and on mobile.' ),
				array( 'Long-term support', 'Scale secure infrastructure and improve the product after launch.' ),
			),
			'cta' => 'Which site process still depends on paper, spreadsheets or disconnected tools?',
		),
		'engineering-software-solutions' => array(
			'label' => 'Engineering',
			'headline' => 'Engineering software built for precision and progress.',
			'hero' => 'Automate reporting, centralise technical data and give engineering teams a dependable view of work, assets and performance.',
			'image' => '/wp-content/uploads/2025/10/Engineering.jpg',
			'note' => 'Production / Assets / Technical data / Field teams',
			'intro_title' => 'Complex workflows deserve purpose-built tools.',
			'intro' => array( 'Engineering firms balance technical accuracy with changing production, asset and customer demands.', 'We create reliable systems that fit those workflows, from CAD-file handling and production dashboards to mobile tools and automated reports.' ),
			'solutions' => array(
				array( '01 / BESPOKE', 'Engineering platforms', 'Build secure operational software around facilities, assets and production processes.', '/services/bespoke-software-development/', 'Explore bespoke software' ),
				array( '02 / INSIGHT', 'Production dashboards', 'See jobs, output, KPIs and exceptions without assembling manual reports.' ),
				array( '03 / FULL STACK', 'Connected applications', 'Combine intuitive interfaces with robust management and data services.', '/services/full-stack-development/', 'Explore full-stack development' ),
				array( '04 / INTEGRATE', 'Legacy integration', 'Connect established tools and databases while improving the user journey around them.' ),
				array( '05 / FIELD', 'Mobile engineering tools', 'Give shop-floor and field teams fast access to the information and actions they need.' ),
			),
			'outcome_heading' => 'More engineering. Less administration.',
			'outcome_copy' => 'Purpose-built software removes avoidable friction while keeping technical teams in control of the details that matter.',
			'outcomes' => array(
				array( 'Automated reporting', 'Generate consistent outputs without repetitive preparation.' ),
				array( 'Centralised data', 'Create one current operational view across teams.' ),
				array( 'Fewer errors', 'Reduce duplicate entry and manual handoffs.' ),
				array( 'Real-time visibility', 'Understand jobs, assets and performance sooner.' ),
				array( 'Built to evolve', 'Scale securely as workflows and customer needs change.' ),
			),
			'cta' => 'Where is manual reporting slowing down your engineering team?',
		),
		'environmental-and-nonprofits' => array(
			'label' => 'Environmental & nonprofits',
			'headline' => 'Digital tools that turn purpose into measurable impact.',
			'hero' => 'Help small teams manage programmes, supporters and evidence with practical technology designed around the mission.',
			'image' => '/wp-content/uploads/2025/10/Environmental.jpg',
			'note' => 'Programmes / Supporters / Fundraising / Impact',
			'intro_title' => 'Make limited resources go further.',
			'intro' => array( 'Environmental groups and nonprofits need to demonstrate impact while delivering programmes and maintaining supporter relationships.', 'We build cost-conscious digital tools that simplify the work behind the mission and create clearer experiences for staff, volunteers, donors and communities.' ),
			'solutions' => array(
				array( '01 / OPERATE', 'Programme platforms', 'Manage operations, donations, volunteers and events without fragmented spreadsheets.' ),
				array( '02 / WEB', 'Mission-led websites', 'Explain the work clearly and turn interest into meaningful action.', '/services/custom-website-development/', 'Explore website development' ),
				array( '03 / MOBILE', 'Community applications', 'Create accessible mobile tools for participation, field activity and supporter engagement.' ),
				array( '04 / IMPACT', 'Impact dashboards', 'Make outcomes and programme data clearer to teams, funders and stakeholders.' ),
				array( '05 / SUPPORT', 'CRM and fundraising tools', 'Improve donor journeys and maintain stronger long-term relationships.' ),
			),
			'outcome_heading' => 'Technology should strengthen the mission.',
			'outcome_copy' => 'Flexible delivery and transparent decisions keep the investment focused on useful outcomes rather than unnecessary complexity.',
			'outcomes' => array(
				array( 'Do more with less', 'Reduce administration for small, busy teams.' ),
				array( 'Stronger outreach', 'Make engagement easier across channels and audiences.' ),
				array( 'Clearer impact', 'Communicate evidence in ways stakeholders can understand.' ),
				array( 'Better donor journeys', 'Remove friction from giving and relationship management.' ),
				array( 'Support that scales', 'Improve the platform as programmes and communities grow.' ),
			),
			'cta' => 'What could your organisation achieve with less digital friction?',
		),
		'enterprise-resource-planning-software' => array(
			'label' => 'Enterprise resource planning',
			'headline' => 'One connected system. A clearer view of the business.',
			'hero' => 'Unify finance, supply chain, HR, sales and operations with ERP software shaped around the way your organisation works.',
			'image' => '/wp-content/uploads/2025/11/Enterprise-Resource-Planning.jpg',
			'note' => 'Finance / Supply chain / HR / Sales / Operations',
			'intro_title' => 'Create one source of operational truth.',
			'intro' => array( 'Disconnected departments and duplicate data make planning slower and create avoidable uncertainty.', 'We design, implement and optimise ERP systems that connect core functions, automate work and provide a reliable real-time view for better decisions.' ),
			'solutions' => array(
				array( '01 / UNIFY', 'Department integration', 'Connect finance, supply chain, HR, sales and operations around consistent data.' ),
				array( '02 / VISIBILITY', 'Business performance', 'Bring KPIs, demand and operational status into one current view.' ),
				array( '03 / AUTOMATE', 'Workflow automation', 'Remove repetitive tasks, bottlenecks and preventable handoff errors.' ),
				array( '04 / SCALE', 'ERP architecture', 'Build a foundation that supports new teams, products and operating models.' ),
				array( '05 / GOVERN', 'Security and compliance', 'Apply appropriate access, safeguards and traceability across business-critical data.' ),
			),
			'outcome_heading' => 'Run the business with fewer blind spots.',
			'outcome_copy' => 'A tailored ERP improves control without forcing every team into processes that do not match reality.',
			'outcomes' => array(
				array( 'Greater efficiency', 'Reduce bottlenecks and duplicated effort.' ),
				array( 'Better forecasting', 'Plan using accurate, timely operational data.' ),
				array( 'More agility', 'Respond faster when markets and demand change.' ),
				array( 'Cost control', 'Understand resources and allocation across departments.' ),
				array( 'Responsive service', 'Give customers and teams more accurate information.' ),
			),
			'cta' => 'Which disconnected process prevents you seeing the whole business?',
		),
		'fitness-and-recreation' => array(
			'label' => 'Fitness & recreation',
			'headline' => 'Digital fitness experiences built to keep people moving.',
			'hero' => 'Connect bookings, memberships, content and performance in mobile-first products that work for customers and operational teams.',
			'image' => '/wp-content/uploads/2025/10/Fitness.jpg',
			'note' => 'Members / Bookings / Facilities / Commerce',
			'intro_title' => 'Designed for movement. Built for growth.',
			'intro' => array( 'Fitness brands, gyms, wellness providers and recreation businesses compete on the quality and convenience of the whole member experience.', 'We create fast, secure platforms that make participation easier while saving staff time and supporting retention across one location or many.' ),
			'solutions' => array(
				array( '01 / MEMBER', 'Member applications', 'Combine bookings, payments, workouts, classes and progress in one intuitive experience.', '/services/mobile-app-development/', 'Explore mobile apps' ),
				array( '02 / SCHEDULE', 'Booking and facilities', 'Coordinate spaces, classes, staff rosters and reservations with less administration.' ),
				array( '03 / GROW', 'Connected websites', 'Turn discovery into membership with SEO-ready journeys linked to operational tools.' ),
				array( '04 / PORTAL', 'Member portals', 'Give users clear access to plans, subscriptions, calendars and performance data.' ),
				array( '05 / COMMERCE', 'Payments and ecommerce', 'Connect products, payments and inventory to the wider member journey.' ),
			),
			'outcome_heading' => 'Make every interaction easier to complete.',
			'outcome_copy' => 'A joined-up experience gives members more control while freeing teams from repetitive coordination.',
			'outcomes' => array(
				array( 'Less scheduling work', 'Automate reservations, reminders and routine changes.' ),
				array( 'Member convenience', 'Put useful actions and information within easy reach.' ),
				array( 'Better retention', 'Maintain engagement beyond each visit or class.' ),
				array( 'Multi-site scale', 'Support boutique studios and growing chains.' ),
				array( 'Reliable experience', 'Deliver consistently across web, iOS and Android.' ),
			),
			'cta' => 'What would make your member experience easier to join and return to?',
		),
		'health-and-safety-software' => array(
			'label' => 'Health & safety',
			'headline' => 'Make safer work easier to manage.',
			'hero' => 'Centralise incidents, inspections, risk and evidence with health and safety software that teams can use wherever work happens.',
			'image' => '/wp-content/uploads/2026/01/healthsafety.jpg',
			'note' => 'Incidents / Inspections / Risk / Compliance',
			'intro_title' => 'Move from paperwork to timely action.',
			'intro' => array( 'Safety depends on accurate information reaching the right people quickly, not on forms waiting to be rekeyed or reviewed.', 'We build custom systems for construction, manufacturing, healthcare, logistics and other environments where reliable reporting and traceability matter.' ),
			'solutions' => array(
				array( '01 / REPORT', 'Incident management', 'Capture, route and track incidents in real time so teams can respond sooner.' ),
				array( '02 / CENTRALISE', 'Safety data systems', 'Replace isolated files and spreadsheets with one controlled record.' ),
				array( '03 / FIELD', 'Mobile inspections', 'Give site teams straightforward inspections and evidence capture on mobile devices.', '/services/mobile-app-development/', 'Explore mobile apps' ),
				array( '04 / RISK', 'Assessments and audits', 'Create consistent digital risk assessments, checks and audit trails.' ),
				array( '05 / CONNECT', 'Operational integration', 'Link safety actions and records with the tools that run the wider operation.' ),
			),
			'outcome_heading' => 'Compliance that supports better work.',
			'outcome_copy' => 'Custom workflows make safety activity more visible without adding unnecessary friction for the people completing it.',
			'outcomes' => array(
				array( 'Faster response', 'Route important incidents and actions without delay.' ),
				array( 'Less paperwork', 'Replace repeated forms and manual data entry.' ),
				array( 'Fewer errors', 'Use consistent fields, checks and controlled records.' ),
				array( 'Easier assurance', 'Maintain evidence for audits and compliance reviews.' ),
				array( 'Ready to scale', 'Adapt the system as teams, sites and obligations change.' ),
			),
			'cta' => 'Which safety process is hardest for your teams to complete consistently?',
		),
		'hospitality-software' => array(
			'label' => 'Hospitality',
			'headline' => 'Connect every team behind the guest experience.',
			'hero' => 'Bring bookings, operations, staff and guest journeys together with hospitality software designed around your venues.',
			'image' => '/wp-content/uploads/2025/12/hospitality.jpg',
			'note' => 'Bookings / Venues / Guests / Multi-site operations',
			'intro_title' => 'Better service starts behind the scenes.',
			'intro' => array( 'Hotels, restaurants, venues and leisure businesses depend on coordinated teams and systems during every customer interaction.', 'We build platforms that reduce administration, connect operational data and scale from boutique brands to multi-site hospitality groups.' ),
			'solutions' => array(
				array( '01 / OPERATE', 'Venue management', 'Coordinate property, housekeeping, staffing and daily operational tasks.' ),
				array( '02 / BOOK', 'Booking and ticketing', 'Create clear reservation journeys for rooms, tables, events and attractions.' ),
				array( '03 / MOBILE', 'Guest and staff apps', 'Put useful actions, updates and service information into focused mobile experiences.' ),
				array( '04 / CONNECT', 'POS and inventory', 'Connect orders, stock and operational systems to reduce errors and shortages.' ),
				array( '05 / SELF SERVICE', 'Digital guest tools', 'Deliver menus, signage, kiosks, loyalty and guest portals around one experience.' ),
			),
			'outcome_heading' => 'Smooth operations create better stays and visits.',
			'outcome_copy' => 'A tailored platform helps staff coordinate confidently and gives guests simpler ways to book, buy and engage.',
			'outcomes' => array(
				array( 'More conversions', 'Reduce friction in booking and purchase journeys.' ),
				array( 'Less administration', 'Automate routine coordination and updates.' ),
				array( 'Connected teams', 'Share current information across front and back of house.' ),
				array( 'Fewer errors', 'Improve stock, order and booking accuracy.' ),
				array( 'Multi-site control', 'Manage consistent operations across locations.' ),
			),
			'cta' => 'Where could a connected platform improve the guest experience?',
		),
		'human-resource-management-software' => array(
			'label' => 'Human resources',
			'headline' => 'HR software designed around how your people work.',
			'hero' => 'Streamline onboarding, workforce records, learning and performance with a secure system shaped around your organisation.',
			'image' => '/wp-content/uploads/2025/10/Human-Resources.jpg',
			'note' => 'Onboarding / Workforce / Compliance / Performance',
			'intro_title' => 'Give HR teams time back for people.',
			'intro' => array( 'Generic HR products often leave important workforce processes spread across forms, inboxes and spreadsheets.', 'We create tailored systems for office, site and remote teams that improve employee journeys while giving HR a dependable operational view.' ),
			'solutions' => array(
				array( '01 / JOIN', 'Onboarding and induction', 'Create clear digital journeys for new starters, site teams and remote employees.' ),
				array( '02 / TIME', 'Time and attendance', 'Manage attendance, timesheets and payroll-ready information more accurately.' ),
				array( '03 / GROW', 'Performance and training', 'Track development, learning and performance activity in one place.' ),
				array( '04 / ASSURE', 'Compliance records', 'Maintain certifications, evidence and renewal activity with clear ownership.' ),
				array( '05 / INSIGHT', 'Workforce dashboards', 'Turn people data into useful metrics for planning and operational decisions.' ),
			),
			'outcome_heading' => 'One workforce view, built for your reality.',
			'outcome_copy' => 'The strongest HR system supports employees and managers while reducing the administration behind every process.',
			'outcomes' => array(
				array( 'Faster onboarding', 'Reduce repeated setup and manual coordination.' ),
				array( 'Better first days', 'Give new starters a clear, consistent experience.' ),
				array( 'Accurate reporting', 'Improve payroll, attendance and compliance information.' ),
				array( 'Visible development', 'Understand training and performance across teams.' ),
				array( 'Remote access', 'Support mobile and distributed workforces securely.' ),
			),
			'cta' => 'Which HR process creates the most repetitive work for your team?',
		),
		'insurance-software' => array(
			'label' => 'Insurance',
			'headline' => 'Modern insurance operations without the legacy friction.',
			'hero' => 'Automate policy, claims and underwriting workflows while improving security and the experience for customers, brokers and teams.',
			'image' => '/wp-content/uploads/2025/12/insurance.jpg',
			'note' => 'Policies / Claims / Underwriting / Customer portals',
			'intro_title' => 'Modernise carefully. Improve what matters.',
			'intro' => array( 'Insurance teams need to move faster while protecting sensitive data and maintaining consistent controls.', 'We build and integrate tailored systems that reduce manual work, improve service and create a scalable route away from fragile legacy processes.' ),
			'solutions' => array(
				array( '01 / MANAGE', 'Claims and policy systems', 'Coordinate cases, policy activity, documents and decisions in one workflow.' ),
				array( '02 / ASSESS', 'Underwriting tools', 'Support consistent, data-informed risk assessment and decision-making.' ),
				array( '03 / SERVE', 'Customer and broker portals', 'Give external users secure, clear access to actions and information.' ),
				array( '04 / PROTECT', 'Security and compliance', 'Apply authentication, encryption, access control and governance to sensitive data.' ),
				array( '05 / INSIGHT', 'Reporting and analytics', 'Understand service, risk and operational performance through focused dashboards.' ),
			),
			'outcome_heading' => 'Build confidence into every insurance workflow.',
			'outcome_copy' => 'Purpose-built software can improve response times and control without forcing a risky all-at-once transformation.',
			'outcomes' => array(
				array( 'Faster responses', 'Move claims and policy actions forward sooner.' ),
				array( 'Less manual work', 'Reduce rekeying, handoffs and preventable errors.' ),
				array( 'Consistent assessment', 'Give underwriting teams structured evidence and workflows.' ),
				array( 'Stronger governance', 'Protect privacy and maintain clear controls.' ),
				array( 'Scalable products', 'Support new products, partners and customer growth.' ),
			),
			'cta' => 'Which legacy insurance workflow is ready for a safer route forward?',
		),
		'legal-industry-software' => array(
			'label' => 'Legal',
			'headline' => 'Secure legal software that keeps every matter moving.',
			'hero' => 'Centralise cases, contracts, documents and compliance with tools designed for legal accuracy, security and client service.',
			'image' => '/wp-content/uploads/2026/01/legal.jpg',
			'note' => 'Matters / Contracts / Documents / Compliance',
			'intro_title' => 'Reduce administration without compromising control.',
			'intro' => array( 'Law firms, in-house teams and compliance departments manage sensitive information against exacting deadlines and obligations.', 'We build tailored platforms that make work easier to find, assign and evidence while supporting secure collaboration from any location.' ),
			'solutions' => array(
				array( '01 / MATTERS', 'Case management', 'Coordinate matters, deadlines, documents and ownership in one current view.' ),
				array( '02 / CONTRACTS', 'Contract lifecycle', 'Track drafting, approval, obligations, renewals and important dates.' ),
				array( '03 / ASSURE', 'Compliance and risk', 'Maintain structured evidence, actions, audit trails and reporting.' ),
				array( '04 / DOCUMENTS', 'Secure collaboration', 'Control, find and share sensitive files across office and remote teams.' ),
				array( '05 / DELIVER', 'Litigation and task tools', 'Plan workloads, coordinate activity and keep client work progressing.' ),
			),
			'outcome_heading' => 'Clarity for teams. Confidence for clients.',
			'outcome_copy' => 'A legal platform should make the right action easier while maintaining the controls every matter requires.',
			'outcomes' => array(
				array( 'Fewer missed deadlines', 'Surface dates, ownership and required actions.' ),
				array( 'Clear audit trails', 'Maintain evidence of decisions and changes.' ),
				array( 'Secure remote work', 'Collaborate without losing document control.' ),
				array( 'Less administration', 'Automate repeatable case and contract activity.' ),
				array( 'Better client service', 'Give teams faster access to complete information.' ),
			),
			'cta' => 'Which legal workflow needs more control and less manual coordination?',
		),
		'logistics-software' => array(
			'label' => 'Logistics',
			'headline' => 'See more. Coordinate faster. Deliver with confidence.',
			'hero' => 'Connect tracking, scheduling, inventory and partner data to give logistics teams a live view of the operation.',
			'image' => '/wp-content/uploads/2025/11/Logistics.jpg',
			'note' => 'Tracking / Routing / Inventory / Delivery',
			'intro_title' => 'Turn movement into useful information.',
			'intro' => array( 'Couriers, distribution networks and supply-chain operators depend on timely decisions across vehicles, inventory, partners and customers.', 'We connect systems and automate workflows so regional delivery businesses and global freight operations can plan and respond with better information.' ),
			'solutions' => array(
				array( '01 / TRACK', 'Real-time visibility', 'Bring location, status and operational data into one dependable view.' ),
				array( '02 / PLAN', 'Scheduling and routing', 'Automate allocation, routes and inventory activity to reduce waste and delays.' ),
				array( '03 / CONNECT', 'Partner integration', 'Move data between suppliers, customers and operational systems reliably.' ),
				array( '04 / FORECAST', 'Demand analytics', 'Use historical and current data to plan resources and capacity.' ),
				array( '05 / INFORM', 'Customer communication', 'Provide clearer tracking, updates and delivery information.' ),
			),
			'outcome_heading' => 'A more visible operation is easier to improve.',
			'outcome_copy' => 'Connected logistics software helps teams act on live conditions instead of reconciling information after the event.',
			'outcomes' => array(
				array( 'Fewer delays', 'Identify exceptions and coordinate action sooner.' ),
				array( 'Lower overhead', 'Reduce manual planning and repeated data entry.' ),
				array( 'Better decisions', 'Plan routes, inventory and resources using current data.' ),
				array( 'Scalable delivery', 'Support more locations, partners and volume.' ),
				array( 'Customer transparency', 'Set clearer expectations with reliable updates.' ),
			),
			'cta' => 'Where does missing or delayed data slow your logistics operation?',
		),
		'manufacturing' => array(
			'label' => 'Manufacturing',
			'headline' => 'Turn production data into stronger operations.',
			'hero' => 'Digitise workflows, connect operational systems and improve visibility from the factory floor to the boardroom.',
			'image' => '/wp-content/uploads/2025/10/Manufacturing.jpg',
			'note' => 'Production / Assets / Inventory / Performance',
			'intro_title' => 'Smarter software. Leaner operations.',
			'intro' => array( 'Manufacturers need accurate information across production, inventory, assets and teams without slowing down the work itself.', 'We create bespoke systems for industrial and engineering environments that replace manual processes with clear, dependable operational tools.' ),
			'solutions' => array(
				array( '01 / PRODUCE', 'Production management', 'Plan and track jobs, tasks and output through the production lifecycle.' ),
				array( '02 / INSIGHT', 'Performance dashboards', 'See throughput, downtime, quality and operational KPIs in real time.' ),
				array( '03 / CONTROL', 'Inventory and assets', 'Track materials, equipment and availability with greater accuracy.' ),
				array( '04 / FIELD', 'Mobile factory tools', 'Give floor and field teams focused applications for the work in front of them.' ),
				array( '05 / CONNECT', 'ERP and legacy integration', 'Connect production with ERP, CRM, databases and established machinery workflows.' ),
			),
			'proof' => array( array( 'APS', 'A central platform for Advanced Process Solutions.' ), array( 'One view', 'Job tracking and task management brought together.' ), array( 'Less manual work', 'Reduced reliance on fragmented day-to-day processes.' ) ),
			'outcome_heading' => 'Build around the factory, not a generic template.',
			'outcome_copy' => 'Purpose-built software can strengthen control and decision-making while respecting the realities of live production.',
			'outcomes' => array(
				array( 'Less administration', 'Automate repeatable production and reporting activity.' ),
				array( 'Accurate data', 'Reduce duplicated entry and inconsistent records.' ),
				array( 'Live visibility', 'See output, issues and priorities as they change.' ),
				array( 'Less waste', 'Identify downtime and process friction sooner.' ),
				array( 'Exact fit', 'Shape the platform around real manufacturing workflows.' ),
			),
			'cta' => 'Which production workflow would benefit from a clearer real-time view?',
		),
		'medtech-and-healthcare' => array(
			'label' => 'MedTech & healthcare',
			'headline' => 'Healthcare software built for trust and better outcomes.',
			'hero' => 'Create secure, accessible clinical and patient products with privacy, evidence and real-world healthcare workflows built in.',
			'image' => '/wp-content/uploads/2025/10/MedTech.jpg',
			'note' => 'Patients / Clinicians / Devices / Health data',
			'intro_title' => 'Technology that supports life-changing work.',
			'intro' => array( 'Healthcare products must be useful to patients and professionals while protecting sensitive information and supporting regulatory obligations.', 'We help providers and MedTech teams move from prototype to dependable platform, integrating clinical workflows and established health systems where needed.' ),
			'solutions' => array(
				array( '01 / DEVICES', 'Connected health platforms', 'Support device tracking, diagnostics and remote monitoring with reliable data flows.' ),
				array( '02 / EXPERIENCE', 'Patient and clinician apps', 'Create accessible mobile and web journeys for care, information and action.', '/services/mobile-app-development/', 'Explore mobile apps' ),
				array( '03 / CLINICAL', 'Workflow tools', 'Improve coordination, task visibility and operational consistency for care teams.' ),
				array( '04 / DATA', 'Health integrations', 'Connect EHR, EMR, labs, portals, payment services and clinical APIs.' ),
				array( '05 / MVP', 'Prototype to product', 'Test the important clinical and user assumptions before scaling the platform.' ),
			),
			'proof' => array( array( 'UK GDPR', 'Privacy-aware architecture and data handling.' ), array( '8-16 weeks', 'Typical timeframe stated for a core MedTech MVP.' ), array( 'GBP 10k+', 'Projects range from focused MVPs to six-figure platforms.' ) ),
			'outcome_heading' => 'Safe foundations for useful healthcare products.',
			'outcome_copy' => 'Security, clinical context and usability need to work together from the earliest product decisions.',
			'outcomes' => array(
				array( 'Better outcomes', 'Design around what patients and professionals need to achieve.' ),
				array( 'Clinical coordination', 'Make responsibilities and information easier to navigate.' ),
				array( 'Protected data', 'Use encryption, audit logging and role-based access.' ),
				array( 'Regulatory awareness', 'Consider NHS DSP Toolkit and relevant medical software obligations.' ),
				array( 'Scalable integration', 'Connect or replace legacy infrastructure carefully.' ),
			),
			'cta' => 'What is the safest practical next step for your healthcare product?',
		),
		'retail-and-e-commerce-software-solutions' => array(
			'label' => 'Retail & ecommerce',
			'headline' => 'Commerce technology built to sell smarter and scale cleanly.',
			'hero' => 'Improve customer journeys and connect inventory, fulfilment and insight across online, high-street and multichannel retail.',
			'image' => '/wp-content/uploads/2025/10/Retail.jpg',
			'note' => 'Storefronts / Mobile / Inventory / Fulfilment',
			'intro_title' => 'Build one joined-up commerce experience.',
			'intro' => array( 'Retail growth depends on the customer journey and the operational systems behind every promise made at checkout.', 'We create technology for global brands and SMEs across fashion, consumer goods, marketplaces and B2B retail, designed for performance and conversion.' ),
			'solutions' => array(
				array( '01 / STOREFRONT', 'Ecommerce websites', 'Create responsive, SEO-ready buying journeys built for speed and conversion.', '/services/custom-website-development/', 'Explore website development' ),
				array( '02 / PLATFORM', 'Commerce integration', 'Customise and connect Shopify, WooCommerce and Magento with wider operations.' ),
				array( '03 / MOBILE', 'Shopping applications', 'Build focused iOS and Android experiences for discovery, purchase and loyalty.' ),
				array( '04 / OPERATE', 'Inventory and fulfilment', 'Coordinate stock, logistics and order workflows with less manual administration.' ),
				array( '05 / INSIGHT', 'Retail analytics', 'Turn customer and operational data into useful real-time dashboards.' ),
			),
			'outcome_heading' => 'Sell smarter. Operate leaner.',
			'outcome_copy' => 'A connected commerce platform improves the experience customers see and the workflows teams rely on behind it.',
			'outcomes' => array(
				array( 'Higher conversion', 'Remove friction from discovery, basket and checkout.' ),
				array( 'Less administration', 'Automate repeatable stock and order activity.' ),
				array( 'Joined-up fulfilment', 'Connect inventory, logistics and customer promises.' ),
				array( 'Useful insight', 'Improve decisions with current customer and ROI data.' ),
				array( 'Performance at scale', 'Stay fast and reliable as demand grows.' ),
			),
			'cta' => 'Where does your customer journey disconnect from retail operations?',
		),
		'travel-management-system-development' => array(
			'label' => 'Travel management',
			'headline' => 'Bring booking, support and spend into one journey.',
			'hero' => 'Centralise organisational travel with systems that simplify booking, expenses, policy compliance and traveller communication.',
			'image' => '/wp-content/uploads/2025/10/Travel.jpg',
			'note' => 'Booking / Expenses / Itineraries / Traveller support',
			'intro_title' => 'Make complex travel easier to coordinate.',
			'intro' => array( 'Corporate, education and healthcare travel involves multiple bookings, policies, changes and reporting responsibilities.', 'We create tailored platforms that integrate with existing workflows, reduce avoidable errors and keep travellers informed when plans change.' ),
			'solutions' => array(
				array( '01 / BOOK', 'Centralised booking', 'Coordinate flights, accommodation and ground transport from one place.' ),
				array( '02 / SPEND', 'Expense integration', 'Connect bookings and expenses for more accurate reporting and control.' ),
				array( '03 / UPDATE', 'Live itineraries', 'Share immediate changes, cancellations and delay information.' ),
				array( '04 / SUPPORT', 'Traveller assistance', 'Provide clear support routes for travellers, including 24/7 service models.' ),
				array( '05 / INSIGHT', 'Travel analytics', 'Understand cost, demand, compliance and programme performance.' ),
			),
			'outcome_heading' => 'More control without a harder traveller experience.',
			'outcome_copy' => 'Connected travel management helps organisations manage policy and spend while making every journey easier to navigate.',
			'outcomes' => array(
				array( 'Fewer errors', 'Reduce duplicated booking and traveller information.' ),
				array( 'Less coordination', 'Automate updates and routine administration.' ),
				array( 'Accurate expenses', 'Connect travel activity with financial records.' ),
				array( 'Policy compliance', 'Guide choices and report against organisational rules.' ),
				array( 'Reduced disruption', 'Keep travellers informed when plans change.' ),
			),
			'cta' => 'Which part of organisational travel creates the most avoidable work?',
		),
		'utilities-and-energy-sector' => array(
			'label' => 'Utilities & energy',
			'headline' => 'Resilient software for critical energy operations.',
			'hero' => 'Modernise field, asset and data workflows with secure platforms built for performance, compliance and sustainability.',
			'image' => '/wp-content/uploads/2025/10/Utilities.jpg',
			'note' => 'Assets / Field teams / IoT / Critical operations',
			'intro_title' => 'Modernise without disrupting essential services.',
			'intro' => array( 'Utilities and energy organisations operate critical infrastructure across assets, field teams, customers and increasingly connected data.', 'We bring experience from regulated sectors to software for asset management, renewable operations, maintenance, smart monitoring and grid workflows.' ),
			'solutions' => array(
				array( '01 / OPERATE', 'Operational platforms', 'Coordinate workforce, maintenance schedules, assets and customer services.' ),
				array( '02 / IOT', 'Sensor integration', 'Turn connected-device and infrastructure data into useful operational signals.' ),
				array( '03 / INSIGHT', 'Real-time dashboards', 'Give teams a current view of performance, risk and emerging issues.' ),
				array( '04 / FIELD', 'Engineer mobile tools', 'Provide secure access and focused workflows wherever field teams are working.' ),
				array( '05 / MODERNISE', 'Legacy transformation', 'Replace or improve established systems through carefully managed stages.' ),
			),
			'outcome_heading' => 'Built for scale, security and sustainability.',
			'outcome_copy' => 'The right architecture supports mission-critical work today while creating a practical route to smarter infrastructure.',
			'outcomes' => array(
				array( 'Operational efficiency', 'Reduce repeated work across assets and teams.' ),
				array( 'Earlier detection', 'Use live data to identify issues sooner.' ),
				array( 'Faster decisions', 'Bring relevant information into one trusted view.' ),
				array( 'Secure field access', 'Support remote work without weakening controls.' ),
				array( 'Careful modernisation', 'Improve critical systems without unnecessary disruption.' ),
			),
			'cta' => 'Which part of your energy technology stack is hardest to evolve safely?',
		),
	);
}

function developyn_render_industry_page() {
	$data = developyn_industry_pages_data();
	$slug = get_post_field( 'post_name', get_queried_object_id() );

	if ( ! isset( $data[ $slug ] ) ) {
		return '';
	}

	$sector = $data[ $slug ];
	$styles = developyn_render_hub_styles();

	ob_start();
	echo $styles; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped
	?>
	<main class="developyn-hub developyn-sector" data-industry-page="<?php echo esc_attr( $slug ); ?>">
		<nav class="developyn-sector__breadcrumb" aria-label="Breadcrumb">
			<a href="<?php echo esc_url( home_url( '/industries/' ) ); ?>">Industries</a><span aria-hidden="true">/</span><span><?php echo esc_html( $sector['label'] ); ?></span>
		</nav>
		<header class="developyn-sector__hero">
			<div>
				<p class="developyn-hub__eyebrow"><?php echo esc_html( $sector['label'] ); ?></p>
				<h1><?php echo esc_html( $sector['headline'] ); ?></h1>
				<p class="developyn-sector__hero-copy"><?php echo esc_html( $sector['hero'] ); ?></p>
				<div class="developyn-sector__actions">
					<a class="developyn-hub__button" href="<?php echo esc_url( home_url( '/contact/' ) ); ?>">Discuss your platform</a>
					<a class="developyn-sector__text-link" href="#industry-solutions">Explore what we build</a>
				</div>
			</div>
			<figure class="developyn-sector__visual">
				<img src="<?php echo esc_url( home_url( $sector['image'] ) ); ?>" alt="" width="1106" height="600" fetchpriority="high">
				<figcaption class="developyn-sector__visual-note"><?php echo esc_html( $sector['note'] ); ?></figcaption>
			</figure>
		</header>

		<section class="developyn-hub__section developyn-sector__intro">
			<h2><?php echo esc_html( $sector['intro_title'] ); ?></h2>
			<div class="developyn-sector__intro-copy">
				<?php foreach ( $sector['intro'] as $paragraph ) : ?><p><?php echo esc_html( $paragraph ); ?></p><?php endforeach; ?>
			</div>
		</section>

		<section id="industry-solutions" class="developyn-hub__section">
			<div class="developyn-hub__section-head">
				<h2>What we build</h2>
				<p>One connected platform or one carefully chosen component, shaped around your workflows, users and goals.</p>
			</div>
			<div class="developyn-sector__solution-grid">
				<?php foreach ( $sector['solutions'] as $solution ) : ?>
					<article class="developyn-sector__solution">
						<span class="developyn-sector__number"><?php echo esc_html( $solution[0] ); ?></span>
						<h3><?php echo esc_html( $solution[1] ); ?></h3>
						<p><?php echo esc_html( $solution[2] ); ?><?php if ( isset( $solution[3], $solution[4] ) ) : ?> <a href="<?php echo esc_url( home_url( $solution[3] ) ); ?>"><?php echo esc_html( $solution[4] ); ?></a>.<?php endif; ?></p>
					</article>
				<?php endforeach; ?>
			</div>
			<?php if ( ! empty( $sector['proof'] ) ) : ?>
				<div class="developyn-sector__proof" aria-label="Selected results and delivery context">
					<?php foreach ( $sector['proof'] as $proof ) : ?><div class="developyn-sector__proof-item"><strong><?php echo esc_html( $proof[0] ); ?></strong><span><?php echo esc_html( $proof[1] ); ?></span></div><?php endforeach; ?>
				</div>
			<?php endif; ?>
		</section>

		<section class="developyn-hub__section developyn-sector__outcomes">
			<div class="developyn-sector__outcome-lead">
				<div><p class="developyn-hub__eyebrow">Why Developyn</p><h2><?php echo esc_html( $sector['outcome_heading'] ); ?></h2></div>
				<p><?php echo esc_html( $sector['outcome_copy'] ); ?></p>
			</div>
			<ul class="developyn-sector__outcome-list">
				<?php foreach ( $sector['outcomes'] as $outcome ) : ?><li><strong><?php echo esc_html( $outcome[0] ); ?></strong><?php echo esc_html( $outcome[1] ); ?></li><?php endforeach; ?>
			</ul>
		</section>

		<section class="developyn-hub__section">
			<div class="developyn-hub__section-head"><h2>From problem to working product</h2><p>A practical route from operational detail to dependable software, with important decisions tested early.</p></div>
			<div class="developyn-sector__process">
				<article class="developyn-sector__step"><h3>Understand</h3><p>Map users, workflows, data, constraints and the friction in the current process.</p></article>
				<article class="developyn-sector__step"><h3>Design and build</h3><p>Prioritise the useful core, test key journeys and connect the systems that matter.</p></article>
				<article class="developyn-sector__step"><h3>Launch and evolve</h3><p>Release with confidence, learn from real use and improve as the operation changes.</p></article>
			</div>
		</section>

		<aside class="developyn-hub__cta">
			<div><p class="developyn-hub__eyebrow">Start with the workflow</p><h2><?php echo esc_html( $sector['cta'] ); ?></h2><p>Bring us the manual process, ageing system or product idea. We will help you identify a practical next step.</p></div>
			<a class="developyn-hub__button" href="<?php echo esc_url( home_url( '/contact/' ) ); ?>">Talk to the team</a>
		</aside>
	</main>
	<?php
	return ob_get_clean();
}

function developyn_render_education_industry() {
	$styles = developyn_render_hub_styles();

	ob_start();
	echo $styles; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped
	?>
	<main class="developyn-hub developyn-sector developyn-sector--education">
		<nav class="developyn-sector__breadcrumb" aria-label="Breadcrumb">
			<a href="<?php echo esc_url( home_url( '/industries/' ) ); ?>">Industries</a><span aria-hidden="true">/</span><span>Education &amp; training</span>
		</nav>
		<header class="developyn-sector__hero">
			<div>
				<p class="developyn-hub__eyebrow">Education &amp; training</p>
				<h1>Learning software built around real people.</h1>
				<p class="developyn-sector__hero-copy">Create digital learning experiences that engage learners, reduce administration and give your team a clearer view of progress.</p>
				<div class="developyn-sector__actions">
					<a class="developyn-hub__button" href="<?php echo esc_url( home_url( '/contact/' ) ); ?>">Discuss your platform</a>
					<a class="developyn-sector__text-link" href="#education-solutions">Explore what we build</a>
				</div>
			</div>
			<figure class="developyn-sector__visual">
				<img src="<?php echo esc_url( home_url( '/wp-content/uploads/2025/10/Education-Training-Industry.jpg' ) ); ?>" alt="A teacher working with children in a classroom" width="1106" height="600" fetchpriority="high">
				<figcaption class="developyn-sector__visual-note">Learning systems &nbsp;/&nbsp; Training portals &nbsp;/&nbsp; Mobile experiences</figcaption>
			</figure>
		</header>

		<section class="developyn-hub__section developyn-sector__intro">
			<h2>Digital infrastructure that helps learning happen.</h2>
			<div class="developyn-sector__intro-copy">
				<p>Education is evolving. Learning providers, training organisations and internal development teams need flexible tools that work for their learners instead of forcing everyone into a rigid template.</p>
				<p>We design custom systems for course delivery, engagement and measurable outcomes, whether learning happens in a classroom, online or in the workplace.</p>
			</div>
		</section>

		<section id="education-solutions" class="developyn-hub__section">
			<div class="developyn-hub__section-head">
				<h2>What we build</h2>
				<p>One connected platform or one carefully chosen component, shaped around your curriculum, workflows and audience.</p>
			</div>
			<div class="developyn-sector__solution-grid">
				<article class="developyn-sector__solution"><span class="developyn-sector__number">01 / LMS</span><h3>Learning management systems</h3><p>Custom platforms for content delivery, progress tracking and learner engagement, aligned with your branding and operating model. See common <a href="https://360learning.com/blog/learning-management-system-examples/">LMS examples</a>.</p></article>
				<article class="developyn-sector__solution"><span class="developyn-sector__number">02 / MOBILE</span><h3>Mobile learning apps</h3><p>Intuitive <a href="<?php echo esc_url( home_url( '/services/mobile-app-development/' ) ); ?>">mobile apps</a> for learners and trainers, including offline access and reliable synchronisation.</p></article>
				<article class="developyn-sector__solution"><span class="developyn-sector__number">03 / INSIGHT</span><h3>Analytics and reporting</h3><p>Real-time dashboards and automated reports for learner performance, completion, engagement and programme oversight.</p></article>
				<article class="developyn-sector__solution"><span class="developyn-sector__number">04 / CONNECT</span><h3>System integrations</h3><p>Connect learning tools with Zoom, Teams, HR systems, payment gateways, CRM software and the data your team already relies on.</p></article>
				<article class="developyn-sector__solution"><span class="developyn-sector__number">05 / TEAMS</span><h3>Internal training portals</h3><p>Secure, straightforward platforms for onboarding and continuous development, built around your people, policies and processes.</p></article>
			</div>
		</section>

		<section class="developyn-hub__section developyn-sector__outcomes">
			<div class="developyn-sector__outcome-lead">
				<div><p class="developyn-hub__eyebrow">Why Developyn</p><h2>A platform should fit the way you teach.</h2></div>
				<p>No rigid templates. We translate learning goals and operational realities into software your learners and administrators can use with confidence.</p>
			</div>
			<ul class="developyn-sector__outcome-list">
				<li><strong>Designed around learners</strong>Journeys, interfaces and content structures matched to your audience and outcomes.</li>
				<li><strong>Secure and scalable</strong>Infrastructure designed to protect data and grow as participation increases.</li>
				<li><strong>Accessible by default</strong>Clear interactions, strong performance and inclusive experience choices.</li>
				<li><strong>Full-stack delivery</strong>Connected front-end experiences and dependable management tools behind them.</li>
				<li><strong>Long-term partnership</strong>Support, updates and improvement planning after the first release.</li>
			</ul>
		</section>

		<section class="developyn-hub__section">
			<div class="developyn-hub__section-head"><h2>From idea to implementation</h2><p>A practical delivery path for a new product or the careful modernisation of an existing learning system.</p></div>
			<div class="developyn-sector__process">
				<article class="developyn-sector__step"><h3>Understand</h3><p>Map learners, administrators, content, evidence needs and the friction in today&rsquo;s process.</p></article>
				<article class="developyn-sector__step"><h3>Design and build</h3><p>Turn priorities into an intuitive product, test the important journeys and integrate the right systems.</p></article>
				<article class="developyn-sector__step"><h3>Launch and evolve</h3><p>Release with confidence, learn from real use and keep improving as your programmes grow.</p></article>
			</div>
		</section>

		<aside class="developyn-hub__cta">
			<div><p class="developyn-hub__eyebrow">Start with the learning goal</p><h2>What would you improve for learners or your team?</h2><p>Bring us the platform idea, manual process or ageing system. We will help you identify a practical next step.</p></div>
			<a class="developyn-hub__button" href="<?php echo esc_url( home_url( '/contact/' ) ); ?>">Talk to the team</a>
		</aside>
	</main>
	<?php
	return ob_get_clean();
}

function developyn_render_industries_hub() {
	$styles     = developyn_render_hub_styles();
	$industries = developyn_industries_data();

	ob_start();
	echo $styles; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped
	?>
	<main class="developyn-hub developyn-industries" data-industry-hub>
		<header class="developyn-hub__hero">
			<p class="developyn-hub__eyebrow">Industry expertise</p>
			<h1>Software shaped around how your industry works.</h1>
			<p class="developyn-hub__hero-copy">Off-the-shelf tools rarely understand the edge cases that make your operation different. We design software around the workflows, evidence and decisions your teams handle every day.</p>
			<ul class="developyn-hub__signals" aria-label="Developyn industry experience">
				<li>18 specialist sectors</li>
				<li>From MVP to modernisation</li>
				<li>UK-based delivery team</li>
			</ul>
		</header>

		<div class="developyn-hub__section">
			<div class="developyn-hub__section-head">
				<h2>Find your sector</h2>
				<p>Explore where we already understand the operational pressures, or talk to us about a workflow that does not fit a standard category.</p>
			</div>
			<div class="developyn-hub__filter-shell">
				<div class="developyn-hub__filters" role="toolbar" aria-label="Filter industries">
					<button class="developyn-hub__filter" type="button" data-sector="all" aria-pressed="true">All industries</button>
					<button class="developyn-hub__filter" type="button" data-sector="built" aria-pressed="false">Built environment</button>
					<button class="developyn-hub__filter" type="button" data-sector="industrial" aria-pressed="false">Industrial &amp; logistics</button>
					<button class="developyn-hub__filter" type="button" data-sector="people" aria-pressed="false">People &amp; services</button>
					<button class="developyn-hub__filter" type="button" data-sector="regulated" aria-pressed="false">Regulated &amp; specialist</button>
				</div>
			</div>
			<p class="developyn-hub__count" aria-live="polite"><span data-industry-count><?php echo count( $industries ); ?></span> sectors shown</p>
			<div class="developyn-industries__grid">
				<?php foreach ( $industries as $industry ) : ?>
					<a class="developyn-industry-card" data-sector="<?php echo esc_attr( $industry['sector'] ); ?>" href="<?php echo esc_url( home_url( $industry['url'] ) ); ?>">
						<figure class="developyn-industry-card__media">
							<img src="<?php echo esc_url( home_url( $industry['image'] ) ); ?>" alt="" loading="lazy" width="1024" height="556">
						</figure>
						<div class="developyn-industry-card__body">
							<span class="developyn-industry-card__sector"><?php echo esc_html( $industry['sector_label'] ); ?></span>
							<h3><?php echo esc_html( $industry['title'] ); ?></h3>
							<p><?php echo esc_html( $industry['summary'] ); ?></p>
							<span class="developyn-industry-card__link"><span>Explore solutions</span><span aria-hidden="true">&rarr;</span></span>
						</div>
					</a>
				<?php endforeach; ?>
			</div>
		</div>

		<aside class="developyn-hub__cta">
			<div>
				<p class="developyn-hub__eyebrow">A different kind of operation?</p>
				<h2>Your workflow matters more than the label.</h2>
				<p>Show us where your current systems create friction and we will help you map a practical route forward.</p>
			</div>
			<a class="developyn-hub__button" href="<?php echo esc_url( home_url( '/contact/' ) ); ?>">Talk through your challenge</a>
		</aside>
	</main>
	<script id="developyn-industries-filter">
	(function(){document.querySelectorAll('[data-industry-hub]').forEach(function(hub){if(hub.dataset.ready)return;hub.dataset.ready='true';var buttons=hub.querySelectorAll('.developyn-hub__filter');var cards=hub.querySelectorAll('.developyn-industry-card');var count=hub.querySelector('[data-industry-count]');buttons.forEach(function(button){button.addEventListener('click',function(){var sector=button.dataset.sector;var visible=0;buttons.forEach(function(item){item.setAttribute('aria-pressed',item===button?'true':'false')});cards.forEach(function(card){var show=sector==='all'||card.dataset.sector===sector;card.hidden=!show;if(show)visible++});count.textContent=visible})})})})();
	</script>
	<?php
	return ob_get_clean();
}

function developyn_insight_category( $post_id ) {
	$categories = get_the_category( $post_id );
	foreach ( $categories as $category ) {
		if ( 'uncategorized' !== $category->slug ) {
			return $category->name;
		}
	}

	return 'Insight';
}

function developyn_insight_excerpt( $post ) {
	$excerpt = get_the_excerpt( $post );
	if ( ! $excerpt ) {
		$excerpt = wp_strip_all_tags( strip_shortcodes( $post->post_content ) );
	}

	return wp_trim_words( $excerpt, 25, '&hellip;' );
}

function developyn_insight_read_time( $post ) {
	$words = str_word_count( wp_strip_all_tags( $post->post_content ) );
	return max( 1, (int) ceil( $words / 220 ) );
}

function developyn_render_insight_card( $post, $variant = 'standard' ) {
	$classes   = 'developyn-insight-card developyn-insight-card--' . sanitize_html_class( $variant );
	$thumbnail = get_the_post_thumbnail( $post->ID, 'large', array( 'loading' => 'lazy', 'alt' => '' ) );
	$category  = developyn_insight_category( $post->ID );
	$minutes   = developyn_insight_read_time( $post );

	ob_start();
	?>
	<article class="<?php echo esc_attr( $classes ); ?>">
		<a href="<?php echo esc_url( get_permalink( $post ) ); ?>">
			<span class="developyn-insight-card__media">
				<?php if ( $thumbnail ) : ?>
					<?php echo $thumbnail; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?>
				<?php else : ?>
					<span class="developyn-insight-card__fallback">Developyn field note</span>
				<?php endif; ?>
			</span>
			<span class="developyn-insight-card__body">
				<span class="developyn-insight-card__meta">
					<span><?php echo esc_html( $category ); ?></span>
					<span aria-hidden="true">/</span>
					<time datetime="<?php echo esc_attr( get_the_date( DATE_W3C, $post ) ); ?>"><?php echo esc_html( get_the_date( 'j M Y', $post ) ); ?></time>
				</span>
				<h2><?php echo esc_html( get_the_title( $post ) ); ?></h2>
				<p><?php echo esc_html( developyn_insight_excerpt( $post ) ); ?></p>
				<span class="developyn-insight-card__read"><?php echo esc_html( $minutes ); ?> min read &nbsp;&rarr;</span>
			</span>
		</a>
	</article>
	<?php
	return ob_get_clean();
}

function developyn_render_insights_hub() {
	$styles = developyn_render_hub_styles();

	$page   = isset( $_GET['insights_page'] ) ? max( 1, absint( $_GET['insights_page'] ) ) : 1;
	$topic  = isset( $_GET['topic'] ) ? sanitize_key( wp_unslash( $_GET['topic'] ) ) : '';
	$search = isset( $_GET['insights_search'] ) ? sanitize_text_field( wp_unslash( $_GET['insights_search'] ) ) : '';
	$args   = array(
		'post_type'           => 'post',
		'post_status'         => 'publish',
		'posts_per_page'      => 12,
		'paged'               => $page,
		'ignore_sticky_posts' => true,
	);

	if ( $topic && get_category_by_slug( $topic ) ) {
		$args['category_name'] = $topic;
	}
	if ( $search ) {
		$args['s'] = $search;
	}

	$query  = new WP_Query( $args );
	$posts  = $query->posts;
	$topics = array(
		''                       => 'All',
		'bespoke-software'       => 'Bespoke software',
		'business-goals'         => 'Business goals',
		'checklists-guides'      => 'Guides',
		'mobile-app-development' => 'Mobile apps',
		'web-strategy'           => 'Web strategy',
	);

	ob_start();
	echo $styles; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped
	?>
	<main class="developyn-hub developyn-insights">
		<header class="developyn-hub__hero">
			<p class="developyn-hub__eyebrow">Developyn insights</p>
			<h1>Ideas for building better digital products.</h1>
			<p class="developyn-hub__hero-copy">Practical thinking for leaders improving operations, replacing fragile systems or turning a promising idea into dependable software.</p>
			<ul class="developyn-hub__signals" aria-label="Insight topics">
				<li>Plain English</li>
				<li>Based on delivery experience</li>
				<li>Written for business decisions</li>
			</ul>
		</header>

		<div class="developyn-insights__tools">
			<nav class="developyn-insights__topics" aria-label="Insight topics">
				<?php foreach ( $topics as $slug => $label ) :
					$url = remove_query_arg( array( 'topic', 'insights_page' ) );
					if ( $slug ) {
						$url = add_query_arg( 'topic', $slug, $url );
					}
					?>
					<a class="developyn-insights__topic" href="<?php echo esc_url( $url ); ?>" <?php echo $topic === $slug ? 'aria-current="page"' : ''; ?>><?php echo esc_html( $label ); ?></a>
				<?php endforeach; ?>
			</nav>
			<form class="developyn-insights__search" method="get" action="<?php echo esc_url( get_permalink() ); ?>">
				<label class="developyn-hub__sr-only" for="developyn-insights-search">Search insights</label>
				<input id="developyn-insights-search" type="search" name="insights_search" value="<?php echo esc_attr( $search ); ?>" placeholder="Search insights">
				<?php if ( $topic ) : ?><input type="hidden" name="topic" value="<?php echo esc_attr( $topic ); ?>"><?php endif; ?>
				<button type="submit">Search</button>
			</form>
		</div>

		<?php if ( $search || $topic ) : ?>
			<p class="developyn-insights__results"><?php echo esc_html( $query->found_posts ); ?> article<?php echo 1 === (int) $query->found_posts ? '' : 's'; ?> found<?php echo $search ? ' for "' . esc_html( $search ) . '"' : ''; ?>.</p>
		<?php endif; ?>

		<?php if ( $posts ) : ?>
			<?php if ( 1 === $page && ! $search && ! $topic ) : ?>
				<div class="developyn-insights__lead-grid">
					<?php echo developyn_render_insight_card( $posts[0], 'featured' ); // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?>
					<div class="developyn-insights__secondary">
						<?php if ( isset( $posts[1] ) ) : echo developyn_render_insight_card( $posts[1], 'compact' ); endif; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?>
						<?php if ( isset( $posts[2] ) ) : echo developyn_render_insight_card( $posts[2], 'compact' ); endif; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?>
					</div>
				</div>
				<?php $posts = array_slice( $posts, 3 ); ?>
			<?php endif; ?>

			<?php if ( $posts ) : ?>
				<div class="developyn-insights__grid">
					<?php foreach ( $posts as $post ) : echo developyn_render_insight_card( $post ); endforeach; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?>
				</div>
			<?php endif; ?>

			<?php if ( $query->max_num_pages > 1 ) :
				$base = str_replace( '999999999', '%#%', esc_url( add_query_arg( 'insights_page', 999999999 ) ) );
				?>
				<nav class="developyn-insights__pagination" aria-label="Insights pagination">
					<?php echo paginate_links( array( 'base' => $base, 'format' => '', 'current' => $page, 'total' => $query->max_num_pages, 'prev_text' => '&larr;', 'next_text' => '&rarr;' ) ); // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?>
				</nav>
			<?php endif; ?>
		<?php else : ?>
			<div class="developyn-insights__empty"><h2>No matching insights yet.</h2><p>Try another topic or a broader search.</p></div>
		<?php endif; ?>

		<aside class="developyn-hub__cta">
			<div>
				<p class="developyn-hub__eyebrow">Turn an idea into action</p>
				<h2>Have a digital problem worth unpacking?</h2>
				<p>Bring us the awkward workflow, unreliable spreadsheet or product idea. We will help you find the practical next step.</p>
			</div>
			<a class="developyn-hub__button" href="<?php echo esc_url( home_url( '/contact/' ) ); ?>">Talk to the team</a>
		</aside>
	</main>
	<?php
	wp_reset_postdata();
	return ob_get_clean();
}
