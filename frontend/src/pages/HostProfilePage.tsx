import { useEffect, useState } from 'react';
import { ArrowLeft, BadgeCheck, Clock3, Languages, Star, UserRound } from 'lucide-react';
import { Link, useParams } from 'react-router-dom';

import { hostApi } from '../lib/api';

type Host = Awaited<ReturnType<typeof hostApi.get>>;

export default function HostProfilePage() {
  const { id } = useParams();
  const [host, setHost] = useState<Host | null>(null);
  const [message, setMessage] = useState('');

  useEffect(() => {
    hostApi.get(Number(id))
      .then(setHost)
      .catch((err) => setMessage(err instanceof Error ? err.message : 'Unable to load host'));
  }, [id]);

  return (
    <main className="profile-page">
      <div className="detail-top">
        <Link to="/" className="back"><ArrowLeft size={18}/>Back</Link>
        <span className="brand">Nestora</span>
      </div>

      {!host ? (
        <div className="profile-shell">{message || 'Loading host…'}</div>
      ) : (
        <section className="profile-shell">
          <div className="host-profile-card">
            <div className="host-avatar">
              {host.avatar_url
                ? <img src={host.avatar_url} alt={host.full_name}/>
                : <UserRound size={46}/>}
            </div>
            <div>
              <span className="eyebrow">Host profile</span>
              <h1>{host.full_name}</h1>
              <p>{host.bio || 'This host has not added a public bio yet.'}</p>
              <div className="host-badges">
                {host.verified_identity && <span><BadgeCheck size={17}/>Identity verified</span>}
                <span><Star size={17}/>{host.average_rating || 'New'} rating</span>
                <span><Clock3 size={17}/>{host.response_time_label}</span>
                <span>{host.response_rate}% response rate</span>
              </div>
            </div>
          </div>

          <div className="profile-facts">
            <div><small>Hosting since</small><strong>{new Date(host.joined_at).toLocaleDateString('en-IN', { year:'numeric', month:'long' })}</strong></div>
            <div><small>Live listings</small><strong>{host.live_listings}</strong></div>
            <div><small>Work</small><strong>{host.work || 'Not shared'}</strong></div>
          </div>

          {host.languages.length > 0 && (
            <div className="panel">
              <h2><Languages size={20}/> Languages</h2>
              <div className="amenity-grid">{host.languages.map((x)=><span key={x}>{x}</span>)}</div>
            </div>
          )}

          {host.interests.length > 0 && (
            <div className="panel">
              <h2>Interests</h2>
              <div className="amenity-grid">{host.interests.map((x)=><span key={x}>{x}</span>)}</div>
            </div>
          )}
        </section>
      )}
    </main>
  );
}
