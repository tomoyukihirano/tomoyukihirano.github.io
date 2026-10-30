source "https://rubygems.org"

# The Windows script pins the patch in .ruby-version; Pages uses Ruby 3.3.x.
ruby "~> 3.3.0"

# Match actions/jekyll-build-pages@v1 (GitHub Pages 232 / Jekyll 3.10.0).
group :jekyll_plugins do
  gem "github-pages", "= 232"
  gem "jekyll-include-cache", "= 0.2.1"
  gem "jekyll-octicons", "~> 14.2"
end

# Ruby 3 no longer bundles the preview web server.
gem "webrick", "~> 1.9"

platforms :windows do
  gem "tzinfo", "~> 1.2"
  gem "tzinfo-data"
end
