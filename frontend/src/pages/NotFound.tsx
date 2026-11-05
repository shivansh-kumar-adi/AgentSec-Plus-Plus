import {Link} from 'react-router-dom'
export function NotFoundPage() { return <main className="standalone-state"><small>404 / ROUTE NOT FOUND</small><h1>This console route does not exist.</h1><p>Return to the authenticated security overview.</p><Link className="primary-button" to="/overview">Open overview</Link></main> }
