const IG_APP_ID = '936619743392459';

export default {
  async fetch(request) {
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Content-Type': 'application/json',
    };

    const url = new URL(request.url);
    const username = url.searchParams.get('username') || 'enginyears.me'

    if (!username) {
      return new Response(
        JSON.stringify({ ok: false, error: 'Missing username param' }),
        { status: 400, headers: corsHeaders }
      );
    }

    try {
      const igRes = await fetch(
        `https://www.instagram.com/api/v1/users/web_profile_info/?username=${username}`,
        {
          headers: {
            'User-Agent':
              'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) ' +
              'AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'en-US,en;q=0.9',
            'X-IG-App-ID': IG_APP_ID,
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': `https://www.instagram.com/${username}/`,
            'Origin': 'https://www.instagram.com',
          },
        }
      );

      if (!igRes.ok) {
        return new Response(
          JSON.stringify({ ok: false, error: `Instagram HTTP ${igRes.status}` }),
          { status: 502, headers: corsHeaders }
        );
      }

      const data = await igRes.json();
      const user = data?.data?.user;

      if (!user) {
        return new Response(
          JSON.stringify({ ok: false, error: 'Invalid response structure' }),
          { status: 502, headers: corsHeaders }
        );
      }

      // Extract recent posts (limit to 5 for sanity)
      const posts = (user.edge_owner_to_timeline_media?.edges || [])
        .slice(0, 5)
        .map(edge => {
          const node = edge.node;
          return {
            id: node.id,
            shortcode: node.shortcode,
            caption: node.edge_media_to_caption?.edges?.[0]?.node?.text || '',
            likes: node.edge_liked_by?.count,
            comments: node.edge_media_to_comment?.count,
            timestamp: node.taken_at_timestamp,
            is_video: node.is_video,
            display_url: node.display_url,
          };
        });

      const response = {
        ok: true,

        // 🔑 Core stats
        stats: {
          followers: user.edge_followed_by?.count,
          following: user.edge_follow?.count,
          posts: user.edge_owner_to_timeline_media?.count,
        },

        // 👤 Profile
        profile: {
          id: user.id,
          username: user.username,
          full_name: user.full_name,
          bio: user.biography,
          profile_pic: user.profile_pic_url_hd,
          category: user.category_name,
          verified: user.is_verified,
          private: user.is_private,
        },

        // 📇 Business info (if exists)
        business: {
          email: user.business_email,
          phone: user.business_phone_number,
          category_enum: user.category_enum,
          external_url: user.external_url,
        },

        // 📸 Content preview
        recent_posts: posts,

        // 🧾 Raw dump (for debugging / future use)
        raw: user,
      };

      return new Response(JSON.stringify(response), {
        status: 200,
        headers: corsHeaders,
      });

    } catch (err) {
      return new Response(
        JSON.stringify({ ok: false, error: err.message }),
        { status: 500, headers: corsHeaders }
      );
    }
  },
};
