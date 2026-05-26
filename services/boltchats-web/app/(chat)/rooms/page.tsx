import { redirect } from 'next/navigation';

// /rooms → redirect to login (client-side guard handles auth check in layout)
export default function RoomsIndexPage(): never {
  redirect('/login');
}
