import { NextResponse } from 'next/server';

export function middleware(request) {
  const authHeader = request.headers.get('authorization');

  // Retrieve secure credentials from environment variables.
  const secureUser = process.env.BASIC_AUTH_USER;
  const securePass = process.env.BASIC_AUTH_PASS;

  // If credentials are not set, simply allow the request.
  if (!secureUser || !securePass) {
    return NextResponse.next();
  }

  if (!authHeader) {
    return new NextResponse('Authorization Required', {
      status: 401,
      headers: {
        'WWW-Authenticate': 'Basic realm="Secure Area"',
      },
    });
  }

  const authValue = authHeader.split(' ')[1];
  const [user, pass] = Buffer.from(authValue, 'base64').toString().split(':');

  if (user === secureUser && pass === securePass) {
    return NextResponse.next();
  } else {
    return new NextResponse('Invalid credentials', { status: 401 });
  }
}

export const config = {
  matcher: '/',
};
