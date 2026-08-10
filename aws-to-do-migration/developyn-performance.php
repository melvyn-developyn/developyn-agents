<?php
/**
 * Plugin Name: Developyn Performance
 * Description: Small, site-specific frontend performance improvements.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

remove_action( 'wp_head', 'wp_print_font_faces', 50 );

add_action(
	'template_redirect',
	static function () {
		ob_start(
			static function ( $html ) {
				return str_replace(
					"document.getElementById('breadcrumb-container').remove();",
					"document.getElementById('breadcrumb-container')?.remove();",
					$html
				);
			}
		);
	},
	0
);

add_action(
	'wp_head',
	static function () {
		$font_base = content_url( 'uploads/fonts/' );
		?>
		<link rel="preload" href="<?php echo esc_url( $font_base . 'V8mQoQDjQSkFtoMM3T6r8E7mF71Q-gOoraIAEj7oUUsmNsFjTDJK.woff2' ); ?>" as="font" type="font/woff2" crossorigin>
		<link rel="preload" href="<?php echo esc_url( $font_base . 'V8mQoQDjQSkFtoMM3T6r8E7mF71Q-gOoraIAEj7aUUsmNsFjTDJK.woff2' ); ?>" as="font" type="font/woff2" crossorigin>
		<link rel="preload" href="<?php echo esc_url( $font_base . 'V8mQoQDjQSkFtoMM3T6r8E7mF71Q-gOoraIAEj4PVksmNsFjTDJK.woff2' ); ?>" as="font" type="font/woff2" crossorigin>
		<style id="developyn-local-fonts">
			body,button,input,select,textarea,h1,h2,h3,h4,h5,h6{font-family:"Space Grotesk",sans-serif!important}
			.home .navburger:before{content:"\2630";font-family:Arial,sans-serif;font-size:1.4em;line-height:1}
			.home img[src*="google_g_icon_download.png"]{width:100px;height:100px;aspect-ratio:1}
			@media(max-width:768px){.o-hide-on-mobile{display:none!important}}
			@media(min-width:769px) and (max-width:1024px){.o-hide-on-tablet{display:none!important}}
			@media(min-width:1025px){.o-hide-on-desktop{display:none!important}}
		</style>
		<?php
	},
	1
);

add_action(
	'wp_head',
	static function () {
		$font_base = content_url( 'uploads/fonts/' );
		?>
		<style id="developyn-font-display">
			@font-face{font-family:"Space Grotesk";font-style:normal;font-weight:400;font-display:optional;src:url("<?php echo esc_url( $font_base . 'V8mQoQDjQSkFtoMM3T6r8E7mF71Q-gOoraIAEj7oUUsmNsFjTDJK.woff2' ); ?>") format("woff2")}
			@font-face{font-family:"Space Grotesk";font-style:normal;font-weight:500;font-display:optional;src:url("<?php echo esc_url( $font_base . 'V8mQoQDjQSkFtoMM3T6r8E7mF71Q-gOoraIAEj7aUUsmNsFjTDJK.woff2' ); ?>") format("woff2")}
			@font-face{font-family:"Space Grotesk";font-style:normal;font-weight:700;font-display:optional;src:url("<?php echo esc_url( $font_base . 'V8mQoQDjQSkFtoMM3T6r8E7mF71Q-gOoraIAEj4PVksmNsFjTDJK.woff2' ); ?>") format("woff2")}
		</style>
		<?php
	},
	100
);

add_filter(
	'style_loader_tag',
	static function ( $html, $handle, $href, $media ) {
		if ( is_front_page() && in_array( $handle, array( 'font-awesome-official', 'font-awesome-official-v4shim' ), true ) ) {
			return '';
		}

		$deferred_styles = array(
			'forminator-module-css-7026',
			'forminator-icons',
			'forminator-utilities',
			'forminator-grid-default',
			'forminator-forms-flat-base',
			'intlTelInput-forminator-css',
			'buttons',
			'forminator-font-roboto',
			'blockslider-preview-style',
			'wpa-css',
			'sp-lc-swiper',
			'sp-lc-font-awesome',
			'sp-lc-style',
			'font-awesome-official',
			'font-awesome-official-v4shim',
			'slb_core',
		);

		if ( ! in_array( $handle, $deferred_styles, true ) ) {
			return $html;
		}

		$media = $media ?: 'all';
		$link  = sprintf(
			'<link rel="stylesheet" href="%1$s" media="print" onload="this.onload=null;this.media=\'%2$s\'">',
			esc_url( $href ),
			esc_attr( $media )
		);

		return $link . '<noscript>' . $html . '</noscript>';
	},
	10,
	4
);

add_action(
	'wp_enqueue_scripts',
	static function () {
		$footer_scripts = array(
			'jquery',
			'jquery-core',
			'jquery-migrate',
			'forminator-jquery-validate',
			'forminator-form',
			'forminator-front-scripts',
			'forminator-intlTelInput',
			'forminator-dompurify',
			'cookie-law-info-wca',
		);

		foreach ( $footer_scripts as $handle ) {
			wp_script_add_data( $handle, 'group', 1 );
		}
	},
	100
);

add_action(
	'wp_head',
	static function () {
		ob_start();
	},
	0
);
add_action(
	'wp_head',
	static function () {
		$head = ob_get_clean();
		$head = str_replace(
			'<script id="cookieyes" type="text/javascript"',
			'<script id="cookieyes" type="text/javascript" defer',
			$head
		);
		$head = str_replace(
			'j.async = true;',
			'j.async = true; j.fetchPriority = "low";',
			$head
		);
		$head = str_replace(
			"j.src = 'https://www.googletagmanager.com/gtm.js?id=' + i + dl;",
			"j.dataset.developynConsentSrc = 'https://www.googletagmanager.com/gtm.js?id=' + i + dl;",
			$head
		);
		$head = str_replace(
			'/wp-content/uploads/2024/07/Frame-10.png',
			'/wp-content/uploads/2024/07/Frame-10.webp',
			$head
		);
		$head = preg_replace(
			'#<link rel="preload" fetchpriority="high" as="image" href="https://developyn\.com/wp-content/uploads/2024/03/vale\.webp"[^>]*>#',
			'',
			$head
		);
		echo $head; // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped
	},
	PHP_INT_MAX
);

add_filter(
	'script_loader_tag',
	static function ( $tag, $handle, $src ) {
		if ( 'google_gtagjs' === $handle ) {
			$tag = str_replace( '<script ', '<script fetchpriority="low" ', $tag );

			return str_replace( ' src=', ' data-developyn-consent-src=', $tag );
		}

		if ( 'forminator-google-recaptcha' !== $handle ) {
			return $tag;
		}

		$src = wp_json_encode( esc_url_raw( $src ) );

		return '<script id="forminator-google-recaptcha-lazy">(function(){var loaded=false;function load(){if(loaded)return;loaded=true;var script=document.createElement("script");script.src=' . $src . ';script.async=true;document.head.appendChild(script)}function observe(){var form=document.querySelector("form.forminator-custom-form");if(!form)return;if("IntersectionObserver" in window){var observer=new IntersectionObserver(function(entries){if(entries[0].isIntersecting){observer.disconnect();load()}},{rootMargin:"800px"});observer.observe(form)}else{load()}form.addEventListener("focusin",load,{once:true})}if(document.readyState==="loading"){document.addEventListener("DOMContentLoaded",observe,{once:true})}else{observe()}}());</script>';
	},
	10,
	3
);

add_action(
	'wp_footer',
	static function () {
		?>
		<script id="developyn-consent-analytics">
		(function(){var loaded=false;function hasConsent(){try{return/(?:analytics|advertisement):yes/.test(decodeURIComponent(document.cookie.match(/(?:^|;\s*)cookieyes-consent=([^;]*)/)?.[1]||""))}catch(e){return false}}function load(){if(loaded||!hasConsent())return;loaded=true;document.querySelectorAll("[data-developyn-consent-src]").forEach(function(script){script.src=script.dataset.developynConsentSrc})}document.addEventListener("cookieyes_consent_update",load);window.addEventListener("cookieyes_consent_update",load);document.addEventListener("click",function(event){if(event.target.closest(".cky-btn-accept,.cky-btn-customize,.cky-btn-reject")){setTimeout(load,300)}});if(document.readyState==="loading"){document.addEventListener("DOMContentLoaded",load,{once:true})}else{load()}}());
		</script>
		<?php
	},
	100
);

add_filter(
	'the_content',
	static function ( $content ) {
		return str_replace(
			array(
				'/wp-content/uploads/2024/08/image-5.png',
				'/wp-content/uploads/2024/08/image-6.png',
				'/wp-content/uploads/2024/07/Frame-10.png',
				'/wp-content/uploads/2025/10/Construction-and-Property-Industry-1024x556.jpg',
				'/wp-content/uploads/2025/10/Engineering-1024x556.jpg',
				'/wp-content/uploads/2025/10/MedTech-1024x556.jpg',
				"document.getElementById('breadcrumb-container').remove();",
			),
			array(
				'/wp-content/uploads/2024/08/image-5.webp',
				'/wp-content/uploads/2024/08/image-6.webp',
				'/wp-content/uploads/2024/07/Frame-10.webp',
				'/wp-content/uploads/2025/10/Construction-and-Property-Industry-1024x556.webp',
				'/wp-content/uploads/2025/10/Engineering-1024x556.webp',
				'/wp-content/uploads/2025/10/MedTech-1024x556.webp',
				"document.getElementById('breadcrumb-container')?.remove();",
			),
			$content
		);
	},
	20
);
