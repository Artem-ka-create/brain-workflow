import Link from "next/link";
import Image from 'next/image';
import Logo from '@/public/icons/logo.png'

const Navbar = () => {
    return (
        <header>
            <nav>
                <Link href='/' className="logo" >
                    <Image src={Logo} alt="logo" width={24} height={24} />
                    <p>DevEvent</p>
                </Link>
                <ul>
                    <Link href="/">Home</Link>
                    <Link href="/">Events</Link>
                    <Link href="/">Create</Link>
                </ul>
            </nav>
        </header>);
}

export default Navbar;
