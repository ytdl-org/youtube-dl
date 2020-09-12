- Q: How to redirect to another extractor?  
  - A:
    - Most simple using only `url_result` 
      ```
      # get proper url first if needed.
      return self.url_result(url)
      ```
    - Using `_request_webpage` and `to_screen` in addition
      ```
      urlh = self._request_webpage(
          url, id, note='Downloading redirect page')
      url = urlh.geturl()
      self.to_screen('Following redirect: %s' % url)
      return self.url_result(url)
      ```
    - Using `return` construction
      ```
      return {
            '_type': 'url_transparent',
            'url': url, 
            'ie_key': ExampleIE.ie_key(),
            'id': id,
        }
      # Alternative if extractor supports internal uri like kaltura
      return {
            '_type': 'url_transparent',
            'url': 'kaltura:%s:%s' % (partner_id, kaltura_id), 
            'ie_key': KalturaIE.ie_key(),
            'id': id,
        }
      ```
