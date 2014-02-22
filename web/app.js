// Create main module
var waveplot = angular.module("waveplot", ['waveplot.directives', 'waveplot.filters', 'ngRoute', 'ngSanitize', 'ui.bootstrap', 'pascalprecht.translate', 'infinite-scroll']);

// Configure the main module
waveplot.config(function ($routeProvider, $locationProvider, $translateProvider, $translatePartialLoaderProvider) {
    // Set up pages in application
    $.each(pages, function (key, value) {
        var match = value[1];
        var info = value[2];
        $routeProvider.when(match, info);
    });

    $routeProvider.otherwise({redirectTo: '/', templateUrl: '/app/home/home.html', controller: HomeCtrl, resolve: HomeCtrl.resolve});

    // Location settings
    $locationProvider.html5Mode(true).hashPrefix('!');

    // Specify the default translations for the menu bar
    $translateProvider.translations('en', {
        "help": "Help",
        "downloads": "Downloads",
        "browse": {
            "top": "Browse",
            "artists": "Artists",
            "albums": "Albums",
            "songs": "Songs",
            "dynamic-range": "Dynamic Range"
        }
    });

    // Set up other translations
    $translateProvider.useLoader('$translatePartialLoader', {
        urlTemplate: '/app/{part}/i18n/{lang}.json'
    });

    $translateProvider.preferredLanguage('en');
});
