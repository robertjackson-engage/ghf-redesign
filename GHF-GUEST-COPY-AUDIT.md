# GHF Site — Guest-Facing Copy Audit
*Every acquisition/guest-oriented element on all 28 pages · prepared for review*

---

## Summary

**114 guest-facing elements** found across **28 pages**.

| Element type | Count | What it is |
|---|---|---|
| **Body copy** | 32 | Sentences in page copy referencing joining, pricing, passes, membership |
| **CTA band** | 28 | Full-width band at page bottom pushing Join / Free Pass |
| **Hero CTA** | 22 | Button in the page hero |
| **Lead form** | 17 | Name/email/phone capture form |
| **Hero subhead** | 13 | Hero paragraph containing acquisition language |
| **Inline link** | 2 | Text link into the funnel |

### Who currently sees this copy

| Visibility | Count | Meaning |
|---|---|---|
| 🔴 **ALWAYS** | 112 | Shown to **guests AND members** — members get sold to |
| 🟢 only-guest | 1 | Correctly hidden from members |
| 🔵 only-member | 1 | Member-only |

> ⚠️ **112 of 114 guest-facing elements are shown to everyone**, including logged-in members. The homepage hero buttons are the *only* guest copy on the entire site that's properly gated — everything else in this document is served to members too.

### The pattern behind the numbers
Three shared components generate most of this copy, so they're also the fastest fix:
- **`cta_band()`** → the 28 "Claim Your Free Pass / Join Online" bands at the bottom of nearly every page
- **`form_section()`** → the 17 lead-capture forms
- **Hero CTAs** → 22 buttons, nearly all pointing at `join.html` or `contact.html#pricing`

Gating those three would resolve ~60% of the items below in a single change.

### Pages ranked by volume of guest copy

| Page | Items |
|---|---|
| `amenities.html` | 9 |
| `seniors.html` | 7 |
| `contact.html` | 6 |
| `corporate-wellness.html` | 6 |
| `bring-a-guest.html` | 5 |
| `cardio.html` | 5 |
| `group-fitness.html` | 5 |
| `kids-club.html` | 5 |
| `pool.html` | 5 |
| `training.html` | 5 |

---

## Page-by-page detail

### `index.html`
**Gainesville Health & Fitness \| The Gym That's Best At Helping Beginners**  ·  3 guest-facing elements

| Type | Copy | Link / detail | Shown to |
|---|---|---|---|
| Hero CTA | Claim Your Free Day Pass → | contact.html#pricing | 🟢 guests |
| Hero CTA | Bring a Friend Free → | bring-a-guest.html | 🔵 members |
| CTA band | Your first day is free — Full access for a day: every class, the pool, the sauna, the coaches — no charge, no obligation, no sales pitch. The only risk is falling in love with the place. | Claim Your Free Pass → → contact.html#pricing \| Join Online Today → → join.html | 🔴 all |

### `join.html`
**Join Online \| Gainesville's Best Gym Memberships \| GHF**  ·  3 guest-facing elements

| Type | Copy | Link / detail | Shown to |
|---|---|---|---|
| Hero CTA | Start My Membership → | #wizard | 🔴 all |
| Hero subhead | Be part of Gainesville's largest, state-of-the-art fitness community, where your membership connects you to expert guidance, innovative programs, and top-tier amenities for both physical and mental well-being. Must be 18 |  | 🔴 all |
| CTA band | Or call (352) 377-4955 today — Not quite ready to join? Try GHF with a free gym pass — there is no charge, no obligation and no risk. | Try GHF For Free → → contact.html#pricing \| Request Pricing & More Info → → contact.html#pricing | 🔴 all |

### `contact.html`
**Contact Us & Get Pricing \| Gainesville Health & Fitness**  ·  6 guest-facing elements

| Type | Copy | Link / detail | Shown to |
|---|---|---|---|
| Hero CTA | Request Gym Pricing → | #pricing | 🔴 all |
| Hero subhead | Tell us your goal and we'll map the membership to match — classes, pool, training, all of it. No pressure, no scripts. Just real people who'd love to show you around. |  | 🔴 all |
| CTA band | We look forward to meeting you — Get ready for an experience that will help you get the most out of life and inspire you to become your best. | Request Pricing → → #pricing | 🔴 all |
| Lead form | #pricing · 01 Request gym pricing · Get pricing for Gainesville's best gym — Complete the form and we will set up a convenient time to present your options. We will contact you via phone, email, or text. One gym membership. Three locatio | button: Request Pricing → | 🔴 all |
| Body copy | Complete the form and we will set up a convenient time to present your options. We will contact you via phone, email, or text. One gym membership. Three locations. |  | 🔴 all |
| Body copy | For membership inquiries please contact memberservices@ghfc.com or call (352) 377-4955. |  | 🔴 all |

### `bring-a-guest.html`
**Bring a Guest \| 6 Free Visits \| GHF**  ·  5 guest-facing elements

| Type | Copy | Link / detail | Shown to |
|---|---|---|---|
| Hero CTA | Join GHF Online → | join.html | 🔴 all |
| Hero CTA | Get Pricing → | contact.html#pricing | 🔴 all |
| Hero subhead | Workouts are better with your favorite humans. Every guest visiting with a member gets 6 free visits — classes, pool, sauna, all of it. Grab your friend; we'll handle the rest. |  | 🔴 all |
| CTA band | The power of friends — Guests are welcome to join the gym online anytime — or grab a free all-access pass and see what GHF is all about. | Join GHF Online → → join.html | 🔴 all |
| Body copy | You may bring as many guests as you'd like during your membership (but just 2 at one time). If you and your guest are unable to work out together, you may request a guest pass. Guests are welcome to join the gym online anytime. |  | 🔴 all |

### `corporate-wellness.html`
**Corporate Wellness \| Gainesville Health & Fitness**  ·  6 guest-facing elements

| Type | Copy | Link / detail | Shown to |
|---|---|---|---|
| Hero CTA | Talk to Our Team → | contact.html#pricing | 🔴 all |
| Hero CTA | See Membership Options → | join.html | 🔴 all |
| Hero subhead | Corporate memberships and on-site wellness that make your people feel their best — and bring that energy back to work. |  | 🔴 all |
| CTA band | Let's build your team's plan — Tell us about your company and we'll put together corporate rates and a wellness plan that fits. No charge, no obligation. | Talk to Our Team → → contact.html#pricing \| Get Pricing → → contact.html#pricing | 🔴 all |
| Inline link | Ask about on-site programs → | contact.html#pricing | 🔴 all |
| Body copy | Teams that move together are healthier, more energized, and more connected. A GHF corporate membership gives your employees the guidance, variety and community that actually keeps them coming back. |  | 🔴 all |

### `amenities.html`
**Best Gym Amenities In One Place \| GHF**  ·  9 guest-facing elements

| Type | Copy | Link / detail | Shown to |
|---|---|---|---|
| Hero CTA | Try Our Amenities for Free → | contact.html#pricing | 🔴 all |
| Hero subhead | Hot yoga studio. Cold plunge. Sauna, steam and hot tub. A 75-foot pool. Free babysitting. Basketball. 900+ classes. Stop piecing together five subscriptions — one membership covers it all. |  | 🔴 all |
| CTA band | More of everything — Ready to start a more fit life? Become a GHF member today for $15 per week. | Claim Your Free Pass → → contact.html#pricing \| Free All-Access Pass → → contact.html#pricing | 🔴 all |
| Lead form | #pass · 08 Request your free guest pass · Your free gym pass is waiting — With your free guest pass, you will have full membership privileges for one day at any Gainesville Health & Fitness location. There is no charge, no obligation | button: Claim Your Free Pass → | 🔴 all |
| Body copy | Your membership isn't a key card — it's an all-access pass. Train, take a class, drop the kids at Kid's Club, shoot hoops, then end in the sauna with a smoothie on the way out. |  | 🔴 all |
| Body copy | Add it up elsewhere and you'd need a gym, a yoga studio, a spa, a pool membership and a babysitter. Here it's one roof, one price, three locations — with a staffed Kid's Club while you train, 24/7 access at Main, indoor courts, an |  | 🔴 all |
| Body copy | Echo offers specialty workshops, GroupFit classes and lifestyle events. We have open gym times for members to use the functional training equipment like tires, sleds, ropes, TRX, rowers and ski ergs, and more. These classes are in |  | 🔴 all |
| Body copy | The gentle embrace of water has long been revered for its healing properties. As you glide through the water, the buoyancy relieves joint stress, promoting flexibility and strengthening muscles. The hydrostatic pressure encourages |  | 🔴 all |
| Body copy | With your free guest pass, you will have full membership privileges for one day at any Gainesville Health & Fitness location. There is no charge, no obligation and no risk. There is, however, a chance that you will be inspired. |  | 🔴 all |

### `blog.html`
**Blog \| GHF**  ·  2 guest-facing elements

| Type | Copy | Link / detail | Shown to |
|---|---|---|---|
| Hero CTA | Join Now → | join.html | 🔴 all |
| CTA band | Come be part of the story — There's always something happening. Come see for yourself. | Claim Your Free Pass → → contact.html#pricing \| Free All-Access Pass → → contact.html#pricing | 🔴 all |

### `cardio.html`
**Cardio Fitness at GHF \| Gainesville Health & Fitness**  ·  5 guest-facing elements

| Type | Copy | Link / detail | Shown to |
|---|---|---|---|
| Hero CTA | Get Your Free All-Access Pass → | #pass | 🔴 all |
| CTA band | Now is the time to get started — Ready to start a more fit life? Become a GHF member today for as little as $15 per week. | Claim Your Free Pass → → contact.html#pricing \| Free All-Access Pass → → contact.html#pricing | 🔴 all |
| Lead form | #pass · 04 Request your free guest pass · Your free all-access pass is waiting — With your free all-access pass, you will have full membership privileges for one day at any Gainesville Health & Fitness location. There is no charge, no obliga | button: Claim My Free Pass → | 🔴 all |
| Body copy | There is something for everyone from beginner to advanced and classes are included in your membership. With three centers to choose from, hundreds of cardio machines, an exciting variety of group exercise classes, and a caring sta |  | 🔴 all |
| Body copy | With your free all-access pass, you will have full membership privileges for one day at any Gainesville Health & Fitness location. There is no charge, no obligation and no risk. There is, however, a chance that you will be inspire |  | 🔴 all |

### `crossfit.html`
**CrossFit at GHF Tioga \| The Pursuit of Optimal Fitness**  ·  4 guest-facing elements

| Type | Copy | Link / detail | Shown to |
|---|---|---|---|
| Hero subhead | Workouts you'd never finish alone become the thing you can't stop talking about. Coaches scale every WOD to your level, and the community learns your name by week one. Open to everyone — no GHF membership required. |  | 🔴 all |
| CTA band | Stronger. Fitter. More confident. — Ready to start a more fit life? Become a GHF member today for as little as $15 per week. | Claim Your Free Pass → → contact.html#pricing \| Free All-Access Pass → → contact.html#pricing | 🔴 all |
| Lead form | #pass · 05 Your free week of CrossFit · Try CrossFit for free — Try CrossFit under the direction of certified CrossFit coaches to teach you the mechanics and safety of W.O.D.s. Try CrossFit in our newly renovated, covered sp | button: Claim My Free Week → | 🔴 all |
| Body copy | Want to see what CrossFit is all about? Try a free trial class and one of our coaches will guide you through a CrossFit workout. Here's what to expect: |  | 🔴 all |

### `faq.html`
**FAQ \| Get The Most Out Of Your Gym Membership \| GHF**  ·  1 guest-facing element

| Type | Copy | Link / detail | Shown to |
|---|---|---|---|
| CTA band | Ready when you are — There is no charge, no obligation and no risk. There is, however, a chance that you will be inspired. | Claim Your Free Pass → → contact.html#pricing \| Free All-Access Pass → → contact.html#pricing | 🔴 all |

### `group-fitness.html`
**Fitness Classes at GHF \| 900+ Group Classes Monthly**  ·  5 guest-facing elements

| Type | Copy | Link / detail | Shown to |
|---|---|---|---|
| CTA band | Come as often as you want — And best of all, these classes are included in your GHF membership. We're here to help you reach your potential. | Claim Your Free Pass → → contact.html#pricing \| Free All-Access Pass → → contact.html#pricing | 🔴 all |
| Lead form | #pass · 04 Request your free fitness class pass · Your free class pass is waiting — With your free class pass, you will have full membership privileges for one day at any Gainesville Health & Fitness location. There is no charge, no obligation | button: Get My Free Class Pass → | 🔴 all |
| Body copy | From beginner to advanced — and classes are included in your membership. Come as often as you want. We're here to help you reach your potential. |  | 🔴 all |
| Body copy | There is something for everyone from beginner to advanced and classes are included in your membership. You may also select from indoor cycling classes every day of the week in our Sky Cycle studio or take classes designed just for |  | 🔴 all |
| Body copy | With your free class pass, you will have full membership privileges for one day at any Gainesville Health & Fitness location. There is no charge, no obligation and no risk. There is, however, a chance that you will be inspired. |  | 🔴 all |

### `hot-yoga.html`
**Hot Yoga Classes \| Three Temperatures, One Stunning Studio \| GHF**  ·  4 guest-facing elements

| Type | Copy | Link / detail | Shown to |
|---|---|---|---|
| Hero subhead | Pick your heat: 85° to ease in, 95° to flow, 105° to find your edge. Gainesville's largest, most advanced hot yoga studio lives inside GHF — and every class is included with membership. |  | 🔴 all |
| CTA band | Join Gainesville's most spacious hot yoga community — Our larger-than-average studio space ensures you have ample room to move and breathe freely. This is more than just a place to sweat; it's a community dedicated to mind/body wellness and holistic health right here in Gainesville. | Claim Your Free Pass → → contact.html#pricing \| Free All-Access Pass → → contact.html#pricing | 🔴 all |
| Lead form | #pass · 05 Get your hot yoga class pass · Relax, recover, rejuvenate — Relax, recover, and rejuvenate with Gainesville's best hot yoga classes in Gainesville's most unique studio. GHF members, you do not need a class pass to attend | button: Get My Hot Yoga Pass → | 🔴 all |
| Body copy | Relax, recover, and rejuvenate with Gainesville's best hot yoga classes in Gainesville's most unique studio. GHF members, you do not need a class pass to attend classes — they are included in your membership! |  | 🔴 all |

### `kids-club.html`
**Kid's Club at GHF \| Free Babysitting While You Work Out**  ·  5 guest-facing elements

| Type | Copy | Link / detail | Shown to |
|---|---|---|---|
| Hero CTA | Get Your Free Pass → | #pass | 🔴 all |
| Hero subhead | Two free hours of trained, attentive childcare every day, at all three clubs — ages 6 weeks to 12 years. The class, the weights, the sauna: they're yours again. Included with every membership. |  | 🔴 all |
| CTA band | Your kids will bring you to the gym — Ready to start a more fit life? Become a GHF member today for as little as $15 per week. | Claim Your Free Pass → → contact.html#pricing \| Free All-Access Pass → → contact.html#pricing | 🔴 all |
| Lead form | #pass · 03 Request your free guest pass · Your free all-access pass is waiting — With your free all-access pass, you will have full membership privileges for one day at any Gainesville Health & Fitness location. There is no charge, no obliga | button: Claim My Free Pass → | 🔴 all |
| Body copy | With your free all-access pass, you will have full membership privileges for one day at any Gainesville Health & Fitness location. There is no charge, no obligation and no risk. There is, however, a chance that you will be inspire |  | 🔴 all |

### `locations.html`
**Locations & Hours \| One Membership, Three Locations \| GHF**  ·  3 guest-facing elements

| Type | Copy | Link / detail | Shown to |
|---|---|---|---|
| Hero CTA | Get Your Free All-Access Pass → | contact.html#pricing | 🔴 all |
| Hero subhead | One membership unlocks all three: the 24/7 flagship on Newberry Road, Gainesville's only women-only club, and the family-friendly Tioga center. Wherever your day takes you, your gym is already there. |  | 🔴 all |
| CTA band | Find the gym that's right for you — Each location is unique and offers a different experience and value. You have access to all 3 locations (GHF Women is women only). | Claim Your Free Pass → → contact.html#pricing \| Free All-Access Pass → → contact.html#pricing | 🔴 all |

### `member-savings.html`
**Member Savings Program \| GHF**  ·  3 guest-facing elements

| Type | Copy | Link / detail | Shown to |
|---|---|---|---|
| Hero CTA | Get Pricing → | contact.html#pricing | 🔴 all |
| CTA band | Your membership pays you back — Ready to start a more fit life? Become a GHF member today for as little as $15 per week. | Claim Your Free Pass → → contact.html#pricing \| Free All-Access Pass → → contact.html#pricing | 🔴 all |
| Body copy | With over 100 participating businesses, you'll save every day on a variety of services and products, no coupons required! Simply show your GHF membership card and start saving. |  | 🔴 all |

### `personal-training.html`
**Personal Training \| I Train For Life \| GHF**  ·  2 guest-facing elements

| Type | Copy | Link / detail | Shown to |
|---|---|---|---|
| CTA band | Now is the time. Start training for life. — Complete the form and we will contact you via phone, email, or text. We look forward to meeting you! | Get Started → → #assessment \| Free All-Access Pass → → contact.html#pricing | 🔴 all |
| Lead form | #assessment · 05 Free fitness assessment & training session · Your first session is on us — You will be matched with a certified personal trainer to assess your abilities, determine your action plan and guide your complimentary training session. Your a | button: Schedule Your Assessment → | 🔴 all |

### `pilates.html`
**Pilates Classes in Gainesville, FL \| GHF**  ·  4 guest-facing elements

| Type | Copy | Link / detail | Shown to |
|---|---|---|---|
| Hero CTA | First Session Free → | #pass | 🔴 all |
| Hero subhead | A stronger core changes how everything feels — your posture, your back, your confidence. Reformer, Tower, Chair and Cadillac with certified instructors who fit the workout to your body. First session free. |  | 🔴 all |
| CTA band | Love the way your body feels — Ready to start a more fit life? Become a GHF member today for as little as $15 per week. | Claim Your Free Pass → → contact.html#pricing \| Free All-Access Pass → → contact.html#pricing | 🔴 all |
| Lead form | #pass · 03 Try Pilates — first session free! · Experience the Pilates difference — Try the Pilates Reformer under the direction of our trained Pilates instructors. They will teach you how to use the reformer, the best technique, and ways to ad | button: Book My Free Session → | 🔴 all |

### `pool.html`
**Indoor Aqua Center \| Aquix by GHF**  ·  5 guest-facing elements

| Type | Copy | Link / detail | Shown to |
|---|---|---|---|
| Hero subhead | A 75-foot heated lap pool. Himalayan salt sauna. Steam, hot tub, warm therapy pool and an arctic plunge. Gainesville's only full-service aqua center — included with membership, every single day. |  | 🔴 all |
| CTA band | Feel good here — From the invigorating cold plunge to the soothing warmth of our facilities and the dynamic energy of our group fitness classes, every aspect of our facility is designed to make you feel good. | Claim Your Free Pass → → contact.html#pricing \| Free All-Access Pass → → contact.html#pricing | 🔴 all |
| Lead form | #pass · 03 Your relaxation experience is a click away · Your free guest pass is waiting — Your guest pass gives you one day privileges to check out the recovery services and studios and gives you access to each gym to try out GHF. There is no charge, | button: Get My Guest Pass → | 🔴 all |
| Body copy | And best of all, these classes are included in your GHF membership. Come as often as you want. We're here to help you reach your potential. |  | 🔴 all |
| Body copy | Your guest pass gives you one day privileges to check out the recovery services and studios and gives you access to each gym to try out GHF. There is no charge, no obligation and no risk. There is, however, a chance that you will |  | 🔴 all |

### `recovery.html`
**Recovery at GHF \| The Holistic Recovery Approach**  ·  4 guest-facing elements

| Type | Copy | Link / detail | Shown to |
|---|---|---|---|
| Hero CTA | Free Guest Pass → | contact.html#pricing | 🔴 all |
| CTA band | Rest is part of the work — Ready to start a more fit life? Become a GHF member today for as little as $15 per week. | Claim Your Free Pass → → contact.html#pricing \| Free All-Access Pass → → contact.html#pricing | 🔴 all |
| Body copy | Discover the restorative power of water in our newly remodeled AQUIX Studio. Swim your way fit in our indoor lap pool, take an aqua class for a joint-friendly workout, and let your muscles and mind recover in the sauna, steam, whi |  | 🔴 all |
| Body copy | You will find healing and restorative elements in all levels of Yoga, Simply Stretch, Tai Chi, Body Flow, Gentle Joints, and Breathing For Life. |  | 🔴 all |

### `seniors.html`
**Senior Fitness Classes \| Fitness For Life \| GHF**  ·  7 guest-facing elements

| Type | Copy | Link / detail | Shown to |
|---|---|---|---|
| Hero CTA | Get Your Free All-Access Pass → | #pass | 🔴 all |
| Hero subhead | Resort-style amenities, classes built for your joints (not against them), and a roomful of friends who'll notice if you miss a Tuesday. Stay strong, stay sharp, stay you. |  | 🔴 all |
| CTA band | Live better. Live longer. — Ready to start a more fit life? Become a GHF member today for as little as $15 per week. | Claim Your Free Pass → → contact.html#pricing \| Free All-Access Pass → → contact.html#pricing | 🔴 all |
| Lead form | #pass · 05 Request your free gym pass · Your free gym pass is waiting — With your free all-access pass, you will have full membership privileges for one day at any Gainesville Health & Fitness location. There is no charge, no obliga | button: Claim My Free Pass → | 🔴 all |
| Body copy | Choose from aqua yoga, gentle joints, balance foundations, pilates flow H2O, and stretch and tone fitness classes. |  | 🔴 all |
| Body copy | All classes on the group fitness schedule are included in membership, there is no additional charge. |  | 🔴 all |
| Body copy | With your free all-access pass, you will have full membership privileges for one day at any Gainesville Health & Fitness location. There is no charge, no obligation and no risk. There is, however, a chance that you will be inspire |  | 🔴 all |

### `special-needs-fitness.html`
**FIT for ALL \| Special Needs Fitness at GHF**  ·  2 guest-facing elements

| Type | Copy | Link / detail | Shown to |
|---|---|---|---|
| CTA band | There's a place for everyone at GHF — Ready to start a more fit life? Become a GHF member today for as little as $15 per week. | Claim Your Free Pass → → contact.html#pricing \| Free All-Access Pass → → contact.html#pricing | 🔴 all |
| Lead form | #pass · 02 Request your free guest pass · Take the first step — Meet with the program coordinator as your first step in Fit For All. You will also be able to try a class to see if the program is right for you. Get ready for | button: Get Started → | 🔴 all |

### `sports-activities.html`
**Sports Activities at GHF \| Basketball, Pool, Cycling & More**  ·  4 guest-facing elements

| Type | Copy | Link / detail | Shown to |
|---|---|---|---|
| Hero CTA | Get Your Free Pass → | #pass | 🔴 all |
| CTA band | Get in the game — Ready to start a more fit life? Become a GHF member today for as little as $15 per week. | Claim Your Free Pass → → contact.html#pricing \| Free All-Access Pass → → contact.html#pricing | 🔴 all |
| Lead form | #pass · 06 Request your free gym fitness pass · Your free all-access pass is waiting — With your free all-access pass, you will have full membership privileges for one day at any Gainesville Health & Fitness location. There is no charge, no obliga | button: Claim My Free Pass → | 🔴 all |
| Body copy | With your free all-access pass, you will have full membership privileges for one day at any Gainesville Health & Fitness location. There is no charge, no obligation and no risk. There is, however, a chance that you will be inspire |  | 🔴 all |

### `strength-training.html`
**Strength Training at GHF \| Largest Strength Gym in Gainesville**  ·  4 guest-facing elements

| Type | Copy | Link / detail | Shown to |
|---|---|---|---|
| CTA band | Built to make you stronger — Ready to start a more fit life? Become a GHF member today for as little as $15 per week. | Claim Your Free Pass → → contact.html#pricing \| Free All-Access Pass → → contact.html#pricing | 🔴 all |
| Lead form | #pass · 07 Request your free guest pass · Enjoy our wide variety of strength training equipment — Check out the gym with the most weight equipment — from benches and barbells to platforms and cables. Your guest pass gives you full membership privileges for o | button: Get My Free Pass → | 🔴 all |
| Body copy | The most important feature of the circuit is our staff. Just look for the friendly people in the blue shirts. They will help set up each weight machine for you, and assist you with every workout, at no extra charge. This service i |  | 🔴 all |
| Body copy | Check out the gym with the most weight equipment — from benches and barbells to platforms and cables. Your guest pass gives you full membership privileges for one day at any Gainesville Health & Fitness location. There is no charg |  | 🔴 all |

### `training.html`
**Signature Training Programs \| GHF**  ·  5 guest-facing elements

| Type | Copy | Link / detail | Shown to |
|---|---|---|---|
| Hero CTA | Request Your Free Trial Workout → | #trial | 🔴 all |
| CTA band | The expertise you need to get better results — Ready to start a more fit life? Become a GHF member today for as little as $15 per week. | Claim Your Free Pass → → contact.html#pricing \| Free All-Access Pass → → contact.html#pricing | 🔴 all |
| Lead form | #trial · 06 Request your free trial workout · Your complimentary workout is a click away — The best way to pick the signature program best for you is to try a complimentary session. Experience the style of workout, environment, and trainer to see if i | button: Request Free Trial → | 🔴 all |
| Inline link | Explore CrossFit During Free Trial Week → | crossfit.html | 🔴 all |
| Body copy | GHF CrossFit is now open to the community. You do not have to be a GHF member to enroll. |  | 🔴 all |

### `tribe.html`
**TRIBE Team Training \| Small Team Training at GHF**  ·  3 guest-facing elements

| Type | Copy | Link / detail | Shown to |
|---|---|---|---|
| Hero CTA | Your First Session Free → | #pass | 🔴 all |
| CTA band | One body. One unit. One tribe. — Ready to start a more fit life? Become a GHF member today for as little as $15 per week. | Claim Your Free Pass → → contact.html#pricing \| Free All-Access Pass → → contact.html#pricing | 🔴 all |
| Lead form | #pass · 06 Realize your greatest strength — train with a team · Get a free sesh for you & a friend — TRIBE Team Training™ gives you a free session to see what it's all about. Pick from LIFE, CORE, PUNCH or FitSTRONG. Complete the form and we will contact you to | button: Claim My Free Session → | 🔴 all |

### `weight-loss.html`
**Weight Loss at GHF \| Accelerate Your Results**  ·  2 guest-facing elements

| Type | Copy | Link / detail | Shown to |
|---|---|---|---|
| Hero CTA | Try GHF For Free → | contact.html#pricing | 🔴 all |
| CTA band | Reaching your goal doesn't have to be a struggle — With three centers to choose from, Gainesville Health & Fitness is here to help you succeed. Become a GHF member today for as little as $15 per week. | Claim Your Free Pass → → contact.html#pricing \| Free All-Access Pass → → contact.html#pricing | 🔴 all |

### `why-ghf.html`
**Why GHF? \| Gainesville Health & Fitness**  ·  5 guest-facing elements

| Type | Copy | Link / detail | Shown to |
|---|---|---|---|
| Hero CTA | Free All-Access Pass → | contact.html#pricing | 🔴 all |
| Hero subhead | Anyone can sell you a membership. GHF is engineered so you'll use yours — more coaching, more variety, more recovery, and more reasons to keep showing up than any gym in Gainesville. |  | 🔴 all |
| CTA band | Come feel it for yourself — A day pass costs you nothing and shows you everything. Bring your gym clothes — leave the doubts at home. | Claim Your Free Pass → → contact.html#pricing \| Free All-Access Pass → → contact.html#pricing | 🔴 all |
| Body copy | The 24/7 flagship for early birds and night owls. A private, women-only club where you can fully be you. A family-friendly Tioga center with kids' programs. One membership opens all three — pick by mood, not by contract. |  | 🔴 all |
| Body copy | No time? Open 24/7. No sitter? Free Kid's Club. Wrong side of town? Three locations. Too sore? Hot tub, sauna and cold plunge are included. The membership is built to remove every reason you'd skip — so you don't. |  | 🔴 all |

### `xforce.html`
**X-Force Body \| Lose Body Fat Fast \| GHF**  ·  3 guest-facing elements

| Type | Copy | Link / detail | Shown to |
|---|---|---|---|
| CTA band | Is X-Force Body right for you? — Try a free X-Force Body session and see if it's right for you. | Claim Your Free Pass → → contact.html#pricing \| Free All-Access Pass → → contact.html#pricing | 🔴 all |
| Lead form | #discovery · 05 Schedule a free discovery session · Your first step to weight loss — Find out how you can build the most muscle and burn the most fat in 25 minutes twice per week. Complete the form and we will contact you to set up your session. | button: Book My Discovery Session → | 🔴 all |
| Body copy | Our secret weapon? The patented X-Force tilting-weight-stack machines that use the most advanced, innovative technology specifically designed to reshape your body in record-breaking time. X-Force Body has been validated through ye |  | 🔴 all |
