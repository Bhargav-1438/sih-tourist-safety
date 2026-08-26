/** 404 fallback for unknown routes. */
import { Link } from "react-router-dom";

export default function NotFoundPage() {
  return (
    <section>
      <h2>404 &mdash; Page not found</h2>
      <p>The route you requested does not exist in this prototype.</p>
      <Link to="/">Back to home</Link>
    </section>
  );
}
