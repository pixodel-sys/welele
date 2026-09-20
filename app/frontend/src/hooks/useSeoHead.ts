import { useEffect } from 'react';

export interface SeoProps {
  title?: string;
  description?: string;
  image?: string;
  url?: string;
  type?: 'website' | 'video.tv_show' | 'video.other' | 'article';
  keywords?: string;
  jsonLd?: Record<string, any>;
}

const DEFAULT_TITLE = 'Welele™ | Stories That Move You';
const DEFAULT_DESC =
  "Welele™ — Stories That Move You. Africa's premier vertical micro-drama storytelling platform. Binge 1-minute African drama series anytime, anywhere.";
const DEFAULT_IMAGE = 'https://welele.tv/brand/welele_mark.png';
const BASE_URL = 'https://welele.tv';

export function useSeoHead({
  title,
  description,
  image,
  url,
  type = 'website',
  keywords,
  jsonLd,
}: SeoProps) {
  useEffect(() => {
    // 1. Page Title
    const formattedTitle = title
      ? title.includes('Welele')
        ? title
        : `${title} | Welele™`
      : DEFAULT_TITLE;
    document.title = formattedTitle;

    // Helper to set or update meta tag by name or property
    const setMetaTag = (attribute: 'name' | 'property', attrValue: string, content: string) => {
      let element = document.querySelector<HTMLMetaElement>(`meta[${attribute}="${attrValue}"]`);
      if (!element) {
        element = document.createElement('meta');
        element.setAttribute(attribute, attrValue);
        document.head.appendChild(element);
      }
      element.setAttribute('content', content);
    };

    const targetDesc = description || DEFAULT_DESC;
    const targetImage = image || DEFAULT_IMAGE;
    const targetUrl = url ? `${BASE_URL}${url.startsWith('/') ? url : `/${url}`}` : BASE_URL;

    // 2. Standard Meta Tags
    setMetaTag('name', 'description', targetDesc);
    if (keywords) {
      setMetaTag('name', 'keywords', keywords);
    }

    // 3. Open Graph Tags
    setMetaTag('property', 'og:title', formattedTitle);
    setMetaTag('property', 'og:description', targetDesc);
    setMetaTag('property', 'og:image', targetImage);
    setMetaTag('property', 'og:url', targetUrl);
    setMetaTag('property', 'og:type', type);

    // 4. Twitter Tags
    setMetaTag('name', 'twitter:title', formattedTitle);
    setMetaTag('name', 'twitter:description', targetDesc);
    setMetaTag('name', 'twitter:image', targetImage);

    // 5. Canonical Link
    let canonical = document.querySelector<HTMLLinkElement>('link[rel="canonical"]');
    if (!canonical) {
      canonical = document.createElement('link');
      canonical.setAttribute('rel', 'canonical');
      document.head.appendChild(canonical);
    }
    canonical.setAttribute('href', targetUrl);

    // 6. Dynamic JSON-LD (if provided)
    let scriptTag: HTMLScriptElement | null = null;
    if (jsonLd) {
      const scriptId = 'dynamic-seo-jsonld';
      scriptTag = document.getElementById(scriptId) as HTMLScriptElement | null;
      if (!scriptTag) {
        scriptTag = document.createElement('script');
        scriptTag.id = scriptId;
        scriptTag.type = 'application/ld+json';
        document.head.appendChild(scriptTag);
      }
      scriptTag.textContent = JSON.stringify(jsonLd);
    }

    return () => {
      // Cleanup dynamic JSON-LD on unmount
      if (scriptTag && scriptTag.parentNode) {
        scriptTag.parentNode.removeChild(scriptTag);
      }
    };
  }, [title, description, image, url, type, keywords, jsonLd]);
}
