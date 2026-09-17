import { Component, type ErrorInfo, type ReactNode } from 'react'
import { Link } from 'react-router-dom'

type Props = { children: ReactNode }
type State = { failed: boolean }

export class ResearchErrorBoundary extends Component<Props, State> {
  state: State = { failed: false }

  static getDerivedStateFromError(): State {
    return { failed: true }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('LabTerra view error', error, info.componentStack)
  }

  render() {
    if (!this.state.failed) return this.props.children

    return <section className="card lab-error-fallback" role="alert">
      <h1>This part of the report could not be displayed</h1>
      <p>The page remains available. The research archive is read independently of this view.</p>
      <div className="toolbar">
        <button type="button" onClick={() => this.setState({ failed: false })}>Try again</button>
        <Link className="button-link" to="/research-archive">Open research archive</Link>
      </div>
    </section>
  }
}
