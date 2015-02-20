if(typeof(voteit) == "undefined"){
  voteit = {};
}

/* Load a dropdown menu
 * 
 * Must follow bootstraps structure of dropdown menus + have the attr data-dropdown-content=(url)
 * The url of data-dropdown-content must be passed to the load_dropdown function
 * 
 * Example:
<button type="button"
    class="btn btn-primary dropdown-toggle cogwheel"
    data-dropdown-content="http://someurl.com"
    aria-expanded="false"
    data-toggle="dropdown"
    onclick="voteit.load_dropdown('http://someurl.com')">
    <span class="glyphicon glyphicon-cog"></span>
</button>
<ul class="dropdown-menu" role="menu">
  <li><a href="#">Loading...</a></li>
</ul>
 */

function load_dropdown(url) {
  var request = arche.do_request(url);
  request.done(function(response) {
    var initiator = $('[data-dropdown-content="' + url + '"');
    var menu = initiator.next();
    menu.html(response);
    initiator.prop( "onclick", null);
  })
}
voteit.load_dropdown = load_dropdown;
