<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:atom="http://www.w3.org/2005/Atom">
  <xsl:output method="html" encoding="utf-8" indent="yes"
              doctype-system="about:legacy-compat"/>

  <xsl:template match="/">
    <html lang="en">
      <head>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1"/>
        <title><xsl:value-of select="/rss/channel/title"/></title>
        <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Petrona:ital,wght@0,400;0,600;0,700;1,400&amp;display=swap"/>
        <style>
          :root {
            --color-stone:    #eeeeea;
            --color-ink:      #1c1a17;
            --color-ink-soft: #5a564f;
            --color-burgundy: #6b1f2c;
          }
          @media (prefers-color-scheme: dark) {
            :root {
              --color-stone:    #181818;
              --color-ink:      #e2e2dd;
              --color-ink-soft: #b0aca0;
              --color-burgundy: #d65a6a;
            }
          }
          *, *::before, *::after { box-sizing: border-box; }
          html, body { margin: 0; padding: 0; }
          body {
            background: var(--color-stone);
            color: var(--color-ink);
            font-family: "Petrona", Georgia, serif;
            font-size: 1.0625rem;
            line-height: 1.6;
            -webkit-font-smoothing: antialiased;
          }
          .feed {
            width: min(680px, 92vw);
            margin: 0 auto;
            padding: 4rem 0;
          }
          .feed-header { margin-bottom: 3rem; }
          .feed-header h1 {
            font-size: 1.75rem;
            font-weight: 700;
            margin: 0 0 0.5rem;
            line-height: 1.2;
          }
          .feed-hint {
            color: var(--color-ink-soft);
            font-size: 0.9375rem;
            font-style: italic;
            margin: 0;
          }
          .feed-items {
            list-style: none;
            margin: 0;
            padding: 0;
            display: flex;
            flex-direction: column;
            gap: 2rem;
          }
          .feed-item article > * { margin: 0; }
          .feed-item h2 {
            font-size: 1.25rem;
            font-weight: 600;
            line-height: 1.3;
            margin-bottom: 0.25rem;
          }
          .feed-item h2 a {
            color: var(--color-ink);
            text-decoration: none;
            border-bottom: 1px solid transparent;
            transition: color 0.15s, border-color 0.15s;
          }
          .feed-item h2 a:hover,
          .feed-item h2 a:focus-visible {
            color: var(--color-burgundy);
            border-bottom-color: var(--color-burgundy);
          }
          .feed-item time {
            display: block;
            color: var(--color-ink-soft);
            font-size: 0.875rem;
            margin-bottom: 0.5rem;
          }
          .feed-item p {
            color: var(--color-ink);
          }
          @media (max-width: 600px) {
            .feed { padding: 2rem 0; }
            .feed-header h1 { font-size: 1.5rem; }
          }
        </style>
      </head>
      <body>
        <main class="feed">
          <header class="feed-header">
            <h1><xsl:value-of select="/rss/channel/title"/></h1>
            <p class="feed-hint">Subscribe in any RSS reader — copy this page's URL.</p>
          </header>
          <ul class="feed-items">
            <xsl:for-each select="/rss/channel/item">
              <li class="feed-item">
                <article>
                  <h2>
                    <a>
                      <xsl:attribute name="href"><xsl:value-of select="link"/></xsl:attribute>
                      <xsl:value-of select="title"/>
                    </a>
                  </h2>
                  <time>
                    <xsl:attribute name="datetime"><xsl:call-template name="pubdate-iso"><xsl:with-param name="rfc822" select="pubDate"/></xsl:call-template></xsl:attribute>
                    <xsl:call-template name="pubdate-display"><xsl:with-param name="rfc822" select="pubDate"/></xsl:call-template>
                  </time>
                  <p><xsl:value-of select="description" disable-output-escaping="yes"/></p>
                </article>
              </li>
            </xsl:for-each>
          </ul>
        </main>
      </body>
    </html>
  </xsl:template>

  <!-- Helper: extract ISO-8601 date from RFC-822 string.
       Input format (fixed by layouts/essays/rss.xml): "Mon, 02 Jan 2006 15:04:05 -0700"
       Positional slicing is safe because the Hugo template emits this exact form.
       Output: "2026-01-02"
  -->
  <xsl:template name="pubdate-iso">
    <xsl:param name="rfc822"/>
    <xsl:variable name="day"   select="substring($rfc822, 6, 2)"/>
    <xsl:variable name="mon3"  select="substring($rfc822, 9, 3)"/>
    <xsl:variable name="year"  select="substring($rfc822, 13, 4)"/>
    <xsl:variable name="month">
      <xsl:choose>
        <xsl:when test="$mon3 = 'Jan'">01</xsl:when>
        <xsl:when test="$mon3 = 'Feb'">02</xsl:when>
        <xsl:when test="$mon3 = 'Mar'">03</xsl:when>
        <xsl:when test="$mon3 = 'Apr'">04</xsl:when>
        <xsl:when test="$mon3 = 'May'">05</xsl:when>
        <xsl:when test="$mon3 = 'Jun'">06</xsl:when>
        <xsl:when test="$mon3 = 'Jul'">07</xsl:when>
        <xsl:when test="$mon3 = 'Aug'">08</xsl:when>
        <xsl:when test="$mon3 = 'Sep'">09</xsl:when>
        <xsl:when test="$mon3 = 'Oct'">10</xsl:when>
        <xsl:when test="$mon3 = 'Nov'">11</xsl:when>
        <xsl:when test="$mon3 = 'Dec'">12</xsl:when>
        <xsl:otherwise>01</xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:value-of select="concat($year, '-', $month, '-', $day)"/>
  </xsl:template>

  <!-- Helper: human-readable date. Reuses the ISO slicing then formats. -->
  <xsl:template name="pubdate-display">
    <xsl:param name="rfc822"/>
    <xsl:variable name="day"   select="substring($rfc822, 6, 2)"/>
    <xsl:variable name="mon3"  select="substring($rfc822, 9, 3)"/>
    <xsl:variable name="year"  select="substring($rfc822, 13, 4)"/>
    <xsl:value-of select="concat($day, ' ', $mon3, ' ', $year)"/>
  </xsl:template>

</xsl:stylesheet>
