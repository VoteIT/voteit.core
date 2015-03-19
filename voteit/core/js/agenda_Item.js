if(typeof(voteit) == "undefined"){
    voteit = {};
}

function set_tag_filter(event) {
  event.preventDefault();
//  console.log(event.target);
}
voteit.set_tag_filter = set_tag_filter;

$(document).ready(function() {
//  $('body').on('click', '[data-set-tag-filter]', voteit.set_tag_filter);
});
