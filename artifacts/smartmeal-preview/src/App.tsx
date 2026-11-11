function App() {
  return (
    <main className="host-shell" aria-label="SmartMeal app preview">
      <header className="host-bar">
        <a className="wordmark" href="/" aria-label="SmartMeal home">
          <span className="wordmark-mark" aria-hidden="true">s</span>
          <span>smartmeal</span>
        </a>
        <span className="host-caption">A little care, every day</span>
        <a
          className="open-link"
          href="/streamlit/"
          target="_blank"
          rel="noreferrer"
        >
          Open app separately
          <span aria-hidden="true">↗</span>
        </a>
      </header>
      <section className="frame-wrap" aria-label="SmartMeal application">
        <iframe
          className="app-frame"
          src="/streamlit/"
          title="SmartMeal nutrition tracker and virtual pet"
          allow="clipboard-read; clipboard-write"
          referrerPolicy="same-origin"
        />
      </section>
      <noscript>
        <p className="no-script">
          SmartMeal needs JavaScript to display here.{' '}
          <a href="/streamlit/">Open the app directly.</a>
        </p>
      </noscript>
    </main>
  );
}

export default App;
