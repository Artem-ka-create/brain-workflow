import EventCard from "@/components/EventCard";
import ExploreBtn from "@/components/ExploreBtn";
import { events } from "@/lib/constants";

export default function Home() {
  return (
      <section>
          <h1 className="text-center">
              The hub for every dev <br /> Event you can&apos;t miss
          </h1>
          <p className="text-center mt-5">HAchatons, Meetings, Conferences, All in ONE Place</p>
          <ExploreBtn />
          <div className="mt-20 space-y-7">
              <h3>Featured Events</h3>

              <ul className="events">
                  {events.map((event) => (
                      <li key={event.title}>
                          <EventCard {...event} />
                      </li>


                  ))}

              </ul>

          </div>


      </section>
  );
}
