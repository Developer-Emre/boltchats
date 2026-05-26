import { redirect } from 'next/navigation';

// Root → always go to login (auth guard in chat layout handles redirect to rooms)
export default function Home(): never {
  redirect('/login');
}
