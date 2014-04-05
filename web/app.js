// Create main module
var waveplot = angular.module("waveplot", ['waveplot.directives', 'waveplot.filters', 'ngRoute', 'ngSanitize', 'ui.bootstrap', 'pascalprecht.translate', 'infinite-scroll']);

// List of pages with unique identifying string ids.
var pages = {
    'help': ['/help', '/help', {templateUrl: '/app/help/help.html', controller: HelpCtrl, resolve: HelpCtrl.resolve}],
    'latest-downloads': ['/latest-downloads', '/latest-downloads', {templateUrl: '/app/downloads/latest.html', controller: LatestDownloadsController, resolve: LatestDownloadsController.resolve}],
    'all-downloads': ['/all-downloads', '/all-downloads', {templateUrl: '/app/downloads/all.html', controller: AllDownloadsController, resolve: AllDownloadsController.resolve}],
    'waveplot-view': ['/waveplot/:uuid', '/waveplot/:uuid', {templateUrl: '/app/view/waveplot.html', controller: WavePlotViewController, resolve: WavePlotViewController.resolve}],
    'register': ['/register', '/register', {templateUrl: '/app/register/register.html', controller: RegisterController, resolve: RegisterController.resolve}]
};

// Configure the main module
waveplot.config(function ($routeProvider, $locationProvider, $translateProvider, $translatePartialLoaderProvider) {
    // Set up pages in application
    $.each(pages, function (key, value) {
        var match = value[1];
        var info = value[2];
        $routeProvider.when(match, info);
    });

    $routeProvider.otherwise({redirectTo: '/', templateUrl: '/app/home/home.html', controller: HomeController, resolve: HomeController.resolve});

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
